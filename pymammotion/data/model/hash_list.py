from dataclasses import dataclass, field
from enum import IntEnum

from mashumaro.mixins.orjson import DataClassORJSONMixin

from pymammotion.proto.mctrl_nav import NavGetCommDataAck, NavGetHashListAck


class PathType(IntEnum):
    """Path types for common data."""

    AREA = 0
    OBSTACLE = 1
    PATH = 2


@dataclass
class FrameList(DataClassORJSONMixin):
    total_frame: int
    data: list[NavGetCommDataAck]


@dataclass
class RootHashList(DataClassORJSONMixin):
    total_frame: int
    data: list[NavGetHashListAck]


@dataclass
class AreaHashNameList(DataClassORJSONMixin):
    """Wrapper so we can serialize to and from dict."""

    name: str
    hash: int


@dataclass
class HashList(DataClassORJSONMixin):
    """stores our map data.
    [hashID, FrameList].
    hashlist for all our hashIDs for verification
    """

    root_hash_list: RootHashList = field(default_factory=RootHashList)
    area: dict = field(default_factory=dict)  # type 0
    path: dict = field(default_factory=dict)  # type 2
    obstacle: dict = field(default_factory=dict)  # type 1
    area_name: list[AreaHashNameList] = field(default_factory=list)

    def update_hash_lists(self, hashlist: list[int]) -> None:
        self.area = {hash_id: frames for hash_id, frames in self.area.items() if hash_id in hashlist}
        self.path = {hash_id: frames for hash_id, frames in self.path.items() if hash_id in hashlist}
        self.obstacle = {hash_id: frames for hash_id, frames in self.obstacle.items() if hash_id in hashlist}

    @property
    def hashlist(self) -> list[int]:
        return [i for obj in self.root_hash_list.data for i in obj.data_couple]

    @property
    def missing_hashlist(self) -> list[int]:
        return [
            i
            for obj in self.root_hash_list.data
            for i in obj.data_couple
            if i not in set(self.area.keys()).union(self.path.keys(), self.obstacle.keys())
        ]

    def update_root_hash_list(self, hash_list: NavGetHashListAck) -> None:
        self.root_hash_list.total_frame = hash_list.total_frame

        for index, obj in enumerate(self.root_hash_list.data):
            if obj.current_frame == hash_list.current_frame:
                # Replace the item if current_frame matches
                self.root_hash_list.data[index] = hash_list
                self.update_hash_lists(self.hashlist)
                return

        # If no match was found, append the new item
        self.root_hash_list.data.append(hash_list)
        self.update_hash_lists(self.hashlist)

    def missing_hash_frame(self):
        return self._find_missing_frames(self.root_hash_list)

    def missing_frame(self, hash_data: NavGetCommDataAck) -> list[int]:
        if hash_data.type == PathType.AREA:
            return self._find_missing_frames(self.area.get(hash_data.hash))

        if hash_data.type == PathType.OBSTACLE:
            return self._find_missing_frames(self.obstacle.get(hash_data.hash))

        if hash_data.type == PathType.PATH:
            return self._find_missing_frames(self.path.get(hash_data.hash))

    def update(self, hash_data: NavGetCommDataAck) -> bool:
        """Update the map data."""
        if hash_data.type == PathType.AREA:
            existing_name = next((area for area in self.area_name if area.hash == hash_data.hash), None)
            if not existing_name:
                self.area_name.append(AreaHashNameList(name=f"area {len(self.area_name)+1}", hash=hash_data.hash))
            return self._add_hash_data(self.area, hash_data)

        if hash_data.type == PathType.OBSTACLE:
            return self._add_hash_data(self.obstacle, hash_data)

        if hash_data.type == PathType.PATH:
            return self._add_hash_data(self.path, hash_data)

    @staticmethod
    def _find_missing_frames(frame_list: FrameList | RootHashList) -> list[int]:
        if frame_list.total_frame == len(frame_list.data):
            return []
        number_list = list(range(1, frame_list.total_frame + 1))

        current_frames = {frame.current_frame for frame in frame_list.data}
        missing_numbers = [num for num in number_list if num not in current_frames]
        return missing_numbers

    @staticmethod
    def _add_hash_data(hash_dict: dict, hash_data: NavGetCommDataAck) -> bool:
        if hash_dict.get(hash_data.hash) is None:
            hash_dict[hash_data.hash] = FrameList(total_frame=hash_data.total_frame, data=[hash_data])
            return True

        if hash_data not in hash_dict[hash_data.hash].data:
            hash_dict[hash_data.hash].data.append(hash_data)
            return True
        return False
