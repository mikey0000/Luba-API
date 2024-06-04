import datetime
import itertools
import json
import queue
import sys
import time
import logging
from asyncio import sleep
from io import BytesIO
from typing import Dict, List

from bleak import BleakClient
from jsonic.serializable import serialize

from pyluba.aliyun.tmp_constant import tmp_constant
from pyluba.bluetooth.const import UUID_WRITE_CHARACTERISTIC
from pyluba.bluetooth.data.convert import parse_custom_data
from pyluba.bluetooth.data.framectrldata import FrameCtrlData
from pyluba.bluetooth.data.notifydata import BlufiNotifyData
from pyluba.data.model import Plan
from pyluba.data.model.execute_boarder import ExecuteBorder
from pyluba.proto import (
    dev_net_pb2,
    luba_msg_pb2,
    luba_mul_pb2,
    mctrl_driver_pb2,
    mctrl_nav_pb2,
    mctrl_ota_pb2,
    mctrl_sys_pb2,
)
from pyluba.utility.constant.device_constant import bleOrderCmd
from pyluba.utility.device_type import DeviceType
from pyluba.utility.rocker_util import RockerControlUtil

_LOGGER = logging.getLogger(__name__)


class BleMessage:
    """Class for sending and recieving messages from Luba"""

    AES_TRANSFORMATION = "AES/CFB/NoPadding"
    DEFAULT_PACKAGE_LENGTH = 20
    DH_G = "2"
    DH_P = "cf5cf5c38419a724957ff5dd323b9c45c3cdd261eb740f69aa94b8bb1a5c96409153bd76b24222d03274e4725a5406092e9e82e9135c643cae98132b0d95f7d65347c68afc1e677da90e51bbab5f5cf429c291b4ba39c6b2dc5e8c7231e46aa7728e87664532cdf547be20c9a3fa8342be6e34371a27c06f7dc0edddd2f86373"
    MIN_PACKAGE_LENGTH = 20
    NEG_SECURITY_SET_ALL_DATA = 1
    NEG_SECURITY_SET_TOTAL_LENGTH = 0
    PACKAGE_HEADER_LENGTH = 4
    mPrintDebug = False
    mWriteTimeout = -1
    mPackageLengthLimit = -1
    mBlufiMTU = -1
    mEncrypted = False
    mChecksum = False
    mRequireAck = False
    mConnectState = 0
    mSendSequence: iter
    mReadSequence: iter
    mAck: queue
    notification: BlufiNotifyData

    def __init__(self, client: BleakClient):
        self.client = client
        self.mSendSequence = itertools.count()
        self.mReadSequence = itertools.count()
        self.mAck = queue.Queue()
        self.notification = BlufiNotifyData()
        

    async def get_report_cfg(self, timeout: int, period: int, no_change_period: int):

        mctlsys = mctrl_sys_pb2.MctlSys(
            todev_report_cfg=mctrl_sys_pb2.report_info_cfg(
                timeout=timeout,
                period=period,
                no_change_period=no_change_period,
                count=1
            )
        )

        mctlsys.todev_report_cfg.sub.append(
            mctrl_sys_pb2.rpt_info_type.RIT_CONNECT
        )
        mctlsys.todev_report_cfg.sub.append(
            mctrl_sys_pb2.rpt_info_type.RIT_RTK
        )
        mctlsys.todev_report_cfg.sub.append(
            mctrl_sys_pb2.rpt_info_type.RIT_DEV_LOCAL
        )
        mctlsys.todev_report_cfg.sub.append(
            mctrl_sys_pb2.rpt_info_type.RIT_WORK
        )
        mctlsys.todev_report_cfg.sub.append(
            mctrl_sys_pb2.rpt_info_type.RIT_DEV_STA
        )
        mctlsys.todev_report_cfg.sub.append(
            mctrl_sys_pb2.rpt_info_type.RIT_VISION_POINT
        )
        mctlsys.todev_report_cfg.sub.append(
            mctrl_sys_pb2.rpt_info_type.RIT_VIO
        )
        mctlsys.todev_report_cfg.sub.append(
            mctrl_sys_pb2.rpt_info_type.RIT_VISION_STATISTIC
        )

        lubaMsg = luba_msg_pb2.LubaMsg()
        lubaMsg.msgtype = luba_msg_pb2.MSG_CMD_TYPE_EMBED_SYS
        lubaMsg.sender = luba_msg_pb2.DEV_MOBILEAPP
        lubaMsg.rcver = luba_msg_pb2.DEV_MAINCTL
        lubaMsg.msgattr = luba_msg_pb2.MSG_ATTR_REQ
        lubaMsg.seqs = 1
        lubaMsg.version = 1
        lubaMsg.subtype = 1
        lubaMsg.sys.CopyFrom(mctlsys)
        byte_arr = lubaMsg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def get_device_base_info(self):
        net = dev_net_pb2.DevNet(
            todev_devinfo_req=dev_net_pb2.DrvDevInfoReq()
        )
        net.todev_devinfo_req.req_ids.add(
            id=1,
            type=6
        )

        lubaMsg = luba_msg_pb2.LubaMsg()
        lubaMsg.msgtype = luba_msg_pb2.MSG_CMD_TYPE_ESP
        lubaMsg.sender = luba_msg_pb2.DEV_MOBILEAPP
        lubaMsg.msgattr = luba_msg_pb2.MSG_ATTR_REQ
        lubaMsg.seqs = 1
        lubaMsg.version = 1
        lubaMsg.subtype = 1
        lubaMsg.net.CopyFrom(net)
        byte_arr = lubaMsg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def get_device_version_main(self):
        commEsp = dev_net_pb2.DevNet(
            todev_devinfo_req=dev_net_pb2.DrvDevInfoReq()
        )

        for i in range(1, 8):
            if (i == 1):
                commEsp.todev_devinfo_req.req_ids.add(
                    id=i,
                    type=6
                )
            commEsp.todev_devinfo_req.req_ids.add(
                id=i,
                type=3
            )

        lubaMsg = luba_msg_pb2.LubaMsg()
        lubaMsg.msgtype = luba_msg_pb2.MSG_CMD_TYPE_ESP
        lubaMsg.sender = luba_msg_pb2.DEV_MOBILEAPP
        lubaMsg.msgattr = luba_msg_pb2.MSG_ATTR_REQ
        lubaMsg.seqs = 1
        lubaMsg.version = 1
        lubaMsg.subtype = 1
        lubaMsg.net.CopyFrom(commEsp)
        byte_arr = lubaMsg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def send_todev_ble_sync(self, sync_type: int):
        net = dev_net_pb2.DevNet(
            todev_ble_sync=sync_type
        )

        byte_arr = self.send_order_msg_net(net)
        await self.post_custom_data_bytes(byte_arr)

    async def set_data_synchronization(self, type: int):
        mctrl_nav = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=12,
                type=type
            )
        )

        lubaMsg = luba_msg_pb2.LubaMsg()
        lubaMsg.msgtype = luba_msg_pb2.MSG_CMD_TYPE_NAV
        lubaMsg.sender = luba_msg_pb2.DEV_MAINCTL
        lubaMsg.rcver = luba_msg_pb2.MSG_ATTR_REQ
        lubaMsg.seqs = 1
        lubaMsg.version = 1
        lubaMsg.subtype = 1
        lubaMsg.nav.CopyFrom(mctrl_nav)
        byte_arr = lubaMsg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def get_hash(self):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_NONE,
            seqs=1,
            version=1,
            subtype=1,
            nav=mctrl_nav_pb2.MctlNav(
                todev_gethash=mctrl_nav_pb2.NavGetHashList(
                    pver=1,
                )
            )
        )

        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def get_all_boundary_hash_list(self, i: int):
        """.getAllBoundaryHashList(3); 0"""
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_NONE,
            seqs=1,
            version=1,
            subtype=1,
            nav=mctrl_nav_pb2.MctlNav(
                todev_gethash=mctrl_nav_pb2.NavGetHashList(
                    pver=1,
                    subCmd=i
                )
            )
        )

        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def get_line_info(self, i: int):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            nav=mctrl_nav_pb2.MctlNav(
                todev_zigzag_ack=mctrl_nav_pb2.NavUploadZigZagResultAck(
                    pver=1,
                    currentHash=i,
                    subCmd=0
                )
            ),
        )
        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def get_hash_response(self, totalFrame: int, currentFrame: int):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            nav=mctrl_nav_pb2.MctlNav(
                todev_gethash=mctrl_nav_pb2.NavGetHashList(
                    pver=1,
                    subCmd=2,
                    action=8,
                    type=3,
                    currentFrame=currentFrame,
                    totalFrame=totalFrame
                )
            )
        )
        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def get_area_tobe_transferred(self):
        commondata = mctrl_nav_pb2.NavGetCommData(
            pver=1,
            subCmd=1,
            action=8,
            type=3
        )

        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            nav=mctrl_nav_pb2.MctlNav(
                todev_get_commondata=commondata
            )
        )
        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def synchronize_hash_data(self, hash_int: int):
        commondata = mctrl_nav_pb2.NavGetCommData(
            pver=1,
            subCmd=1,
            action=8,
            Hash=hash_int
        )

        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            nav=mctrl_nav_pb2.MctlNav(
                todev_get_commondata=commondata
            )
        )
        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def get_task(self):
        hash_map = {"pver": 1, "subCmd": 2, "result": 0}
        await self.post_custom_data(self.get_json_string(bleOrderCmd.task, hash_map))

    async def send_ble_alive(self):
        hash_map = {"ctrl": 1}
        await self.post_custom_data(self.get_json_string(bleOrderCmd.bleAlive, hash_map))

    async def start_work_job(self):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            nav=mctrl_nav_pb2.MctlNav(
                todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(
                    type=1,
                    action=1,
                    result=0
                )
            )
        )

        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def read_plan(self, i: int):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            nav=mctrl_nav_pb2.MctlNav(
                todev_planjob_set=mctrl_nav_pb2.NavPlanJobSet(
                    subCmd=i,
                )
            )
        )
        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    # (2, 0);
    async def read_plan(self, i: int, i2: int):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            nav=mctrl_nav_pb2.MctlNav(
                todev_planjob_set=mctrl_nav_pb2.NavPlanJobSet(
                    subCmd=i,
                    planIndex=i2
                )
            )
        )
        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def read_plan_unable_time(self, i):
        build = mctrl_nav_pb2.NavUnableTimeSet()
        build.subCmd = i

        luba_msg = luba_msg_pb2.LubaMsg()
        luba_msg.msgtype = luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV
        luba_msg.sender = luba_msg_pb2.MsgDevice.DEV_MOBILEAPP
        luba_msg.rcver = luba_msg_pb2.MsgDevice.DEV_MAINCTL
        luba_msg.msgattr = luba_msg_pb2.MsgAttr.MSG_ATTR_REQ
        luba_msg.seqs = 1
        luba_msg.version = 1
        luba_msg.subtype = 1
        luba_msg.nav.todev_unable_time_set.CopyFrom(build)

        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def send_plan2(self, plan: Plan):
        navPlanJobSet = luba_msg_pb2.NavPlanJobSet()
        navPlanJobSet.pver = plan.pver
        navPlanJobSet.subCmd = plan.subCmd
        navPlanJobSet.area = plan.area
        navPlanJobSet.deviceId = plan.deviceId
        navPlanJobSet.workTime = plan.workTime
        navPlanJobSet.version = plan.version
        navPlanJobSet.id = plan.id
        navPlanJobSet.userId = plan.userId
        navPlanJobSet.planId = plan.planId
        navPlanJobSet.taskId = plan.taskId
        navPlanJobSet.jobId = plan.jobId
        navPlanJobSet.startTime = plan.startTime
        navPlanJobSet.endTime = plan.endTime
        navPlanJobSet.week = plan.week
        navPlanJobSet.knifeHeight = plan.knifeHeight
        navPlanJobSet.model = plan.model
        navPlanJobSet.edgeMode = plan.edgeMode
        navPlanJobSet.requiredTime = plan.requiredTime
        navPlanJobSet.routeAngle = plan.routeAngle
        navPlanJobSet.routeModel = plan.routeModel
        navPlanJobSet.routeSpacing = plan.routeSpacing
        navPlanJobSet.ultrasonicBarrier = plan.ultrasonicBarrier
        navPlanJobSet.totalPlanNum = plan.totalPlanNum
        navPlanJobSet.planIndex = plan.planIndex
        navPlanJobSet.result = plan.result
        navPlanJobSet.speed = plan.speed
        navPlanJobSet.taskName = plan.taskName
        navPlanJobSet.jobName = plan.jobName
        navPlanJobSet.zoneHashs.extend(plan.zoneHashs)
        navPlanJobSet.reserved = plan.reserved

        luba_msg = luba_msg_pb2.luba_msg()
        luba_msg.msgtype = luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV
        luba_msg.sender = luba_msg_pb2.MsgDevice.DEV_MOBILEAPP
        luba_msg.rcver = luba_msg_pb2.MsgDevice.DEV_MAINCTL
        luba_msg.msgattr = luba_msg_pb2.MsgAttr.MSG_ATTR_REQ
        luba_msg.seqs = 1
        luba_msg.version = 1
        luba_msg.subtype = 1
        luba_msg.nav.todevPlanjobSet.CopyFrom(navPlanJobSet)

        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    def get_reserved(self, generate_route_information):
        return bytes([generate_route_information.path_order, generate_route_information.obstacle_laps]).decode('utf-8')

    async def generate_route_information(self, generate_route_information):
        """How you start a manual job, then call startjob"""

        nav_req_cover_path = mctrl_nav_pb2.NavReqCoverPath()
        nav_req_cover_path.pver = 1
        nav_req_cover_path.subCmd = 0
        nav_req_cover_path.zoneHashs.extend(
            generate_route_information.one_hashs)
        nav_req_cover_path.jobMode = generate_route_information.job_mode  # grid type
        nav_req_cover_path.edgeMode = generate_route_information.edge_mode  # border laps
        nav_req_cover_path.knifeHeight = generate_route_information.knife_height
        nav_req_cover_path.speed = generate_route_information.speed
        nav_req_cover_path.ultraWave = generate_route_information.ultra_wave
        nav_req_cover_path.channelWidth = generate_route_information.channel_width  # mow width
        nav_req_cover_path.channelMode = generate_route_information.channel_mode
        nav_req_cover_path.toward = generate_route_information.toward
        nav_req_cover_path.reserved = self.get_reserved(
            generate_route_information)  # grid or border first

        luba_msg = luba_msg_pb2.LubaMsg()
        luba_msg.msgtype = luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV
        luba_msg.sender = luba_msg_pb2.MsgDevice.DEV_MOBILEAPP
        luba_msg.rcver = luba_msg_pb2.MsgDevice.DEV_MAINCTL
        luba_msg.msgattr = luba_msg_pb2.MsgAttr.MSG_ATTR_REQ
        luba_msg.seqs = 1
        luba_msg.version = 1
        luba_msg.subtype = 1

        mctl_nav = mctrl_nav_pb2.MctlNav()
        mctl_nav.bidire_reqconver_path.CopyFrom(nav_req_cover_path)
        luba_msg.nav.CopyFrom(mctl_nav)

        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def start_work_order(self, job_id, job_ver, rain_tactics, job_mode, knife_height, speed, ultra_wave,
                               channel_width, channel_mode):
        """Pretty sure this starts a job too but isn't used"""
        luba_msg = luba_msg_pb2.LubaMsg()
        luba_msg.msgtype = luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV
        luba_msg.sender = luba_msg_pb2.MsgDevice.DEV_MOBILEAPP
        luba_msg.rcver = luba_msg_pb2.MsgDevice.DEV_MAINCTL
        luba_msg.msgattr = luba_msg_pb2.MsgAttr.MSG_ATTR_REQ
        luba_msg.seqs = 1
        luba_msg.version = 1
        luba_msg.subtype = 1

        nav = mctrl_nav_pb2.MctlNav()
        start_job = mctrl_nav_pb2.NavStartJob()
        start_job.jobId = job_id
        start_job.jobVer = job_ver
        start_job.rainTactics = rain_tactics
        start_job.jobMode = job_mode
        start_job.knifeHeight = knife_height
        start_job.speed = speed
        start_job.ultraWave = ultra_wave
        start_job.channelWidth = channel_width
        start_job.channelMode = channel_mode

        nav.todev_mow_task.CopyFrom(start_job)
        luba_msg.nav.CopyFrom(nav)

        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def breakPointContinue(self):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            nav=mctrl_nav_pb2.MctlNav(
                todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(
                    type=1,
                    action=7,
                    result=0
                )
            )
        )
        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def breakPointAnywhereContinue(self, refresh_loading: bool):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            nav=mctrl_nav_pb2.MctlNav(
                todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(
                    type=1,
                    action=9,
                    result=0
                )
            )
        )
        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    def clearNotification(self):
        self.notification = None
        self.notification = BlufiNotifyData()

    # async def get_device_info(self):
    #     await self.postCustomData(self.getJsonString(bleOrderCmd.getDeviceInfo))

    async def send_device_info(self):
        """Currently not called"""
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_ESP,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_COMM_ESP,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            net=dev_net_pb2.DevNet(
                todev_ble_sync=1,
                todev_devinfo_req=dev_net_pb2.DrvDevInfoReq()
            )
        )
        byte_arr = luba_msg.SerializeToString()
        await self.post_custom_data_bytes(byte_arr)

    async def requestDeviceStatus(self):
        request = False
        type = self.getTypeValue(0, 5)
        try:
            request = await self.post(BleMessage.mEncrypted, BleMessage.mChecksum, False, type, None)
            # print(request)
        except Exception as err:
            # Log.w(TAG, "post requestDeviceStatus interrupted")
            request = False
            print(err)

        # if not request:
        #     onStatusResponse(BlufiCallback.CODE_WRITE_DATA_FAILED, null)

    async def requestDeviceVersion(self):
        request = False
        type = self.getTypeValue(0, 7)
        try:
            request = await self.post(BleMessage.mEncrypted, BleMessage.mChecksum, False, type, None)
            # print(request)
        except Exception as err:
            # Log.w(TAG, "post requestDeviceStatus interrupted")
            request = False
            print(err)

    def pause_execute_task(self):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            nav=mctrl_nav_pb2.MctlNav(
                todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(
                    type=1,
                    action=2,
                    result=0
                )
            )
        )

        byte_array = luba_msg.SerializeToString()

    async def return_to_dock(self):
        mctrlNav = mctrl_nav_pb2.MctlNav()
        navTaskCtrl = mctrl_nav_pb2.NavTaskCtrl()
        navTaskCtrl.type = 1
        navTaskCtrl.action = 5
        navTaskCtrl.result = 0
        mctrlNav.todev_taskctrl.CopyFrom(navTaskCtrl)

        lubaMsg = luba_msg_pb2.LubaMsg()
        lubaMsg.msgtype = luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV
        lubaMsg.sender = luba_msg_pb2.MsgDevice.DEV_MOBILEAPP
        lubaMsg.rcver = luba_msg_pb2.MsgDevice.DEV_MAINCTL
        lubaMsg.msgattr = luba_msg_pb2.MsgAttr.MSG_ATTR_REQ
        lubaMsg.seqs = 1
        lubaMsg.version = 1
        lubaMsg.subtype = 1
        lubaMsg.nav.CopyFrom(mctrlNav)
        bytes = lubaMsg.SerializeToString()
        await self.post_custom_data_bytes(bytes)

    async def leave_dock(self):
        mctrlNav = mctrl_nav_pb2.MctlNav()
        mctrlNav.todev_one_touch_leave_pile = 1

        lubaMsg = luba_msg_pb2.LubaMsg()
        lubaMsg.msgtype = luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV
        lubaMsg.sender = luba_msg_pb2.DEV_MOBILEAPP
        lubaMsg.rcver = luba_msg_pb2.DEV_MAINCTL
        lubaMsg.seqs = 1
        lubaMsg.version = 1
        lubaMsg.subtype = 1
        lubaMsg.nav.CopyFrom(mctrlNav)
        bytes = lubaMsg.SerializeToString()
        await self.post_custom_data_bytes(bytes)

    async def setBladeControl(self, onOff: int):
        mctlsys = mctrl_sys_pb2.MctlSys()
        sysKnifeControl = mctrl_sys_pb2.SysKnifeControl()
        sysKnifeControl.knifeStatus = onOff
        mctlsys.todev_knife_ctrl.CopyFrom(sysKnifeControl)

        lubaMsg = luba_msg_pb2.LubaMsg()
        lubaMsg.msgtype = luba_msg_pb2.MSG_CMD_TYPE_EMBED_SYS
        lubaMsg.sender = luba_msg_pb2.DEV_MOBILEAPP
        lubaMsg.rcver = luba_msg_pb2.DEV_MAINCTL
        lubaMsg.msgattr = luba_msg_pb2.MSG_ATTR_REQ
        lubaMsg.seqs = 1
        lubaMsg.version = 1
        lubaMsg.subtype = 1
        lubaMsg.sys.CopyFrom(mctlsys)
        bytes = lubaMsg.SerializeToString()
        await self.post_custom_data_bytes(bytes)

    async def start_job(self, blade_height):
        """Call after calling generate_route_information I think"""
        await self.set_knife_height(blade_height)
        await self.start_work_job()

    async def transformSpeed(self, linear: float, percent: float):

        transfrom3 = RockerControlUtil.getInstance().transfrom3(linear, percent)
        if (transfrom3 is not None and len(transfrom3) > 0):
            linearSpeed = transfrom3[0] * 10
            angularSpeed = (int)(transfrom3[1] * 4.5)

            await self.send_control(linearSpeed, angularSpeed)

    async def transformBothSpeeds(self, linear: float, angular: float, linearPercent: float, angularPercent: float):
        transfrom3 = RockerControlUtil.getInstance().transfrom3(linear, linearPercent)
        transform4 = RockerControlUtil.getInstance().transfrom3(angular, angularPercent)

        if (transfrom3 != None and len(transfrom3) > 0):
            linearSpeed = transfrom3[0] * 10
            angularSpeed = (int)(transform4[1] * 4.5)
            print(linearSpeed, angularSpeed)
            await self.send_control(linearSpeed, angularSpeed)

    # asnyc def transfromDoubleRockerSpeed(float f, float f2, boolean z):
    #         transfrom3 = RockerControlUtil.getInstance().transfrom3(f, f2)
    #         if (transfrom3 != null && transfrom3.size() > 0):
    #             if (z):
    #                 this.linearSpeed = transfrom3.get(0).intValue() * 10
    #             else
    #                 this.angularSpeed = (int) (transfrom3.get(1).intValue() * 4.5d)

    #         if (this.countDownTask == null):
    #             testSendControl()

    async def sendBorderPackage(self, executeBorder: ExecuteBorder):
        await self.post_custom_data(serialize(executeBorder))

    async def post_custom_data_bytes(self, data: bytes):
        if (data == None):
            return
        type_val = self.getTypeValue(1, 19)
        try:
            suc = await self.post(self.mEncrypted, self.mChecksum, self.mRequireAck, type_val, data)
            # int status = suc ? 0 : BlufiCallback.CODE_WRITE_DATA_FAILED
            # onPostCustomDataResult(status, data)
            # print(suc)
        except Exception as err:
            print(err)

    async def post_custom_data(self, data_str: str):
        data = data_str.encode()
        if (data == None):
            return
        type_val = self.getTypeValue(1, 19)
        try:
            suc = await self.post(self.mEncrypted, self.mChecksum, self.mRequireAck, type_val, data)
            # int status = suc ? 0 : BlufiCallback.CODE_WRITE_DATA_FAILED
            # onPostCustomDataResult(status, data)
        except Exception as err:
            print(err)

    def getTypeValue(self, type: int, subtype: int):
        return (subtype << 2) | type

    async def post(self, encrypt: bool, checksum: bool, require_ack: bool, type_of: int, data: bytes) -> bool:
        if data is None:
            return await self.post_non_data(encrypt, checksum, require_ack, type_of)

        return await self.post_contains_data(encrypt, checksum, require_ack, type_of, data)

    async def gatt_write(self, data: bytes) -> None:
        await self.client.write_gatt_char(UUID_WRITE_CHARACTERISTIC, data, True)

    async def post_non_data(self, encrypt: bool, checksum: bool, require_ack: bool, type_of: int) -> bool:
        sequence = self.generateSendSequence()
        postBytes = self.getPostBytes(type_of, encrypt, checksum, require_ack, False, sequence, None)
        posted = await self.gatt_write(postBytes)
        return posted and (not require_ack or self.receiveAck(sequence))

    async def post_contains_data(self, encrypt: bool, checksum: bool, require_ack: bool, type_of: int,
                                 data: bytes) -> bool:
        chunk_size = 517  # self.client.mtu_size - 3

        chunks = list()
        for i in range(0, len(data), chunk_size):
            if (i + chunk_size > len(data)):
                chunks.append(data[i: len(data)])
            else:
                chunks.append(data[i: i + chunk_size])
        for index, chunk in enumerate(chunks):
            frag = index != len(chunks) - 1
            sequence = self.generateSendSequence()
            postBytes = self.getPostBytes(type_of, encrypt, checksum, require_ack, frag, sequence, chunk)
            # print("sequence")
            # print(sequence)
            posted = await self.gatt_write(postBytes)
            if (posted != None):
                return False

            if (not frag):
                return not require_ack or self.receiveAck(sequence)

            if (require_ack and not self.receiveAck(sequence)):
                return False
            else:
                print("sleeping 0.01")
                await sleep(0.01)

    def getPostBytes(self, type: int, encrypt: bool, checksum: bool, require_ack: bool, hasFrag: bool, sequence: int,
                     data: bytes) -> bytes:

        byteOS = BytesIO()
        dataLength = (0 if data == None else len(data))
        frameCtrl = FrameCtrlData.getFrameCTRLValue(
            encrypt, checksum, 0, require_ack, hasFrag)
        byteOS.write(type.to_bytes(1, sys.byteorder))
        byteOS.write(frameCtrl.to_bytes(1, sys.byteorder))
        byteOS.write(sequence.to_bytes(1, sys.byteorder))
        byteOS.write(dataLength.to_bytes(1, sys.byteorder))

        if (data != None):
            byteOS.write(data)

        print(byteOS.getvalue())
        return byteOS.getvalue()

    def parseNotification(self, response: bytearray):
        dataOffset = None
        if (response is None):
            # Log.w(TAG, "parseNotification null data");
            return -1

        # if (this.mPrintDebug):
        #     Log.d(TAG, "parseNotification Notification= " + Arrays.toString(response));
        # }
        if (len(response) >= 4):
            sequence = int(response[2])  # toInt
            if sequence != next(self.mReadSequence):
                print("parseNotification read sequence wrong", sequence, self.mReadSequence)
                self.mReadSequence = itertools.count(start=sequence)
                # this is questionable
                # self.mReadSequence = sequence
                # self.mReadSequence_2.incrementAndGet()

            # LogUtil.m7773e(self.mGatt.getDevice().getName() + "打印丢包率", self.mReadSequence_2 + "/" + self.mReadSequence_1);
            pkt_type = int(response[0])  # toInt
            pkgType = self._getPackageType(pkt_type)
            subType = self._getSubType(pkt_type)
            self.notification.setType(pkt_type)
            self.notification.setPkgType(pkgType)
            self.notification.setSubType(subType)
            frameCtrl = int(response[1])  # toInt
            # print("frame ctrl")
            # print(frameCtrl)
            # print(response)
            # print(f"pktType {pkt_type} pkgType {pkgType} subType {subType}")
            self.notification.setFrameCtrl(frameCtrl)
            frameCtrlData = FrameCtrlData(frameCtrl)
            dataLen = int(response[3])  # toInt specifies length of data

            try:
                dataBytes = response[4: 4 + dataLen]
                if frameCtrlData.isEncrypted():
                    print("is encrypted")
                #     BlufiAES aes = new BlufiAES(self.mAESKey, AES_TRANSFORMATION, generateAESIV(sequence));
                #     dataBytes = aes.decrypt(dataBytes);
                # }
                if (frameCtrlData.isChecksum()):
                    print("checksum")
                #     int respChecksum1 = toInt(response[response.length - 1]);
                #     int respChecksum2 = toInt(response[response.length - 2]);
                #     int crc = BlufiCRC.calcCRC(BlufiCRC.calcCRC(0, new byte[]{(byte) sequence, (byte) dataLen}), dataBytes);
                #     int calcChecksum1 = (crc >> 8) & 255;
                #     int calcChecksum2 = crc & 255;
                #     if (respChecksum1 != calcChecksum1 || respChecksum2 != calcChecksum2) {
                #         Log.w(TAG, "parseNotification: read invalid checksum");
                #         if (self.mPrintDebug) {
                #             Log.d(TAG, "expect   checksum: " + respChecksum1 + ", " + respChecksum2);
                #             Log.d(TAG, "received checksum: " + calcChecksum1 + ", " + calcChecksum2);
                #             return -4;
                #         }
                #         return -4;
                #     }
                # }
                if (frameCtrlData.hasFrag()):
                    dataOffset = 2
                else:
                    dataOffset = 0

                self.notification.addData(dataBytes, dataOffset)
                return 1 if frameCtrlData.hasFrag() else 0
            except Exception as e:
                print(e)
                return -100

        # Log.w(TAG, "parseNotification data length less than 4");
        return -2

    async def parseBlufiNotifyData(self, return_bytes: bool = False):
        pkgType = self.notification.getPkgType()
        subType = self.notification.getSubType()
        dataBytes = self.notification.getDataArray()
        if (pkgType == 0):
            # never seem to get these..
            self._parseCtrlData(subType, dataBytes)
        if (pkgType == 1):
            if return_bytes: return dataBytes
            return await self._parseDataData(subType, dataBytes)

    def _parseCtrlData(self, subType: int, data: bytes):
        pass
        # self._parseAck(data)

    async def _parseDataData(self, subType: int, data: bytes):
        #     if (subType == 0) {
        #         this.mSecurityCallback.onReceiveDevicePublicKey(data);
        #         return;
        #     }
        print(subType)
        match subType:
            #         case 15:
            #             parseWifiState(data);
            #             return;
            #         case 16:
            #             parseVersion(data);
            #             return;
            #         case 17:
            #             parseWifiScanList(data);
            #             return;
            #         case 18:
            #             int errCode = data.length > 0 ? 255 & data[0] : 255;
            #             onError(errCode);
            #             return;
            case 19:
                #             # com/agilexrobotics/utils/EspBleUtil$BlufiCallbackMain.smali
                luba_msg = parse_custom_data(data)  # parse to protobuf message
                # really need some sort of callback
                if luba_msg.HasField('net'):
                    if luba_msg.net.HasField('toapp_wifi_iot_status'):
                        # await sleep(1.5)
                        await self.send_todev_ble_sync(2)
                return luba_msg

    # private void parseCtrlData(int i, byte[] bArr) {
    #     if (i == 0) {
    #         parseAck(bArr);
    #     }
    # }

    # private void parseAck(byte[] bArr) {
    #     this.mAck.add(Integer.valueOf(bArr.length > 0 ? bArr[0] & 255 : 256));
    # }

    def receiveAck(self, expectAck: int) -> bool:
        try:
            ack = next(self.mAck)
            return ack == expectAck
        except Exception as err:
            print(err)
            return False

    def generateSendSequence(self):
        return next(self.mSendSequence) & 255

    def getJsonString(self, cmd: int) -> str:
        jSONObject = {}
        try:
            jSONObject["cmd"] = cmd
            jSONObject[tmp_constant.REQUEST_ID] = int(time.time())
            return json.dumps(jSONObject)
        except Exception:

            return ""

    def get_json_string(self, cmd: int, hash_map: Dict[str, object]) -> str:
        jSONObject = {}
        try:
            jSONObject["cmd"] = cmd
            jSONObject[tmp_constant.REQUEST_ID] = int(time.time())
            jSONObject2 = {}
            for key, value in hash_map.items():
                jSONObject2[key] = value
            jSONObject["params"] = jSONObject2
            return json.dumps(jSONObject)
        except Exception as e:
            print(e)
            return ""

    def current_milli_time(self):
        return round(time.time() * 1000)

    def _getTypeValue(self, type: int, subtype: int):
        return (subtype << 2) | type

    def _getPackageType(self, typeValue: int):
        return typeValue & 3

    def _getSubType(self, typeValue: int):
        return (typeValue & 252) >> 2

    # === sendOrderMsg_Net  ===

    def send_order_msg_net(self, build):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_ESP,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_COMM_ESP,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            net=build)

        return luba_msg.SerializeToString()

    def get_4g_module_info(self):
        build = dev_net_pb2.DevNet(
            todev_get_mnet_cfg_req=dev_net_pb2.DevNet().todev_get_mnet_cfg_req)
        print("Send command -- Get device 4G network module information")
        self.send_order_msg_net(build)


    def get_4g_info(self):
        build = dev_net_pb2.DevNet(
            TodevMnetInfoReq=dev_net_pb2.DevNet().TodevMnetInfoReq)
        print("Send command -- Get device 4G network information")
        self.send_order_msg_net(build)

    def set_zmq_enable(self):
        build = dev_net_pb2.DevNet(
            todev_set_dds2_zmq=dev_net_pb2.DrvDebugDdsZmq(
                is_enable=True,
                rx_topic_name="perception_post_result",
                tx_zmq_url="tcp://0.0.0.0:5555"
            )
        )
        print("Send command -- Set vision ZMQ to enable")
        self.send_order_msg_net(build)

    def set_iot_setting(self, iot_conctrl_type: dev_net_pb2.iot_conctrl_type):
        build = dev_net_pb2.DevNet(TodevSetIotOfflineReq=iot_conctrl_type)
        print("Send command -- Device re-online")
        self.send_order_msg_net(build)

    def set_device_log_upload(self, request_id: str, operation: int, server_ip: int, server_port: int, number: int, type: int):
        build = dev_net_pb2.DrvUploadFileToAppReq(
            biz_id=request_id,
            operation=operation,
            server_ip=server_ip,
            server_port=server_port,
            num=number,
            type=type
        )
        print(
            f"Send log====Feedback====Command======requestID:{request_id} operation:{operation} serverIp:{server_ip} type:{type}")
        self.send_order_msg_net(dev_net_pb2.DevNet(
            todev_ble_sync=1, todev_uploadfile_req=build))

    def set_device_socket_request(self, request_id: str, operation: int, server_ip: int, server_port: int, number: int, type: int) -> None:
        """Set device socket request (bluetooth only)."""
        build = dev_net_pb2.DrvUploadFileToAppReq(
            biz_id=request_id,
            operation=operation,
            server_ip=server_ip,
            server_port=server_port,
            num=number,
            type=type
        )
        print(
            f"Send log====Feedback====Command======requestID:{request_id}  operation:{operation} serverIp:{server_ip}  type:{type}")
        self.send_order_msg_net(dev_net_pb2.DevNet(
            todev_ble_sync=1, todev_uploadfile_req=build))

    def get_device_log_info(self, biz_id: str, type: int, log_url: str) -> None:
        """Get device log info (bluetooth only)."""
        self.send_order_msg_net(
            dev_net_pb2.DevNet(
                todev_ble_sync=1,
                todev_req_log_info=dev_net_pb2.DrvUploadFileReq(
                    biz_id=biz_id,
                    type=type,
                    url=log_url,
                    num=0,
                    user_id="" # TODO supply user id
                )
            )
        )

    def cancel_log_update(self, biz_id: str):
        """Cancel log update (bluetooth only)."""
        self.send_order_msg_net(dev_net_pb2.DevNet(
            todev_log_data_cancel=dev_net_pb2.DrvUploadFileCancel(biz_id=biz_id)))

    def get_device_network_info(self):
        build = dev_net_pb2.DevNet(
            todev_networkinfo_req=dev_net_pb2.GetNetworkInfoReq(req_ids=1))
        print("Send command - get device network information")
        self.send_order_msg_net(build)

    def set_device_4g_enable_status(self, new_4g_status: bool):
        build = dev_net_pb2.DevNet(
            todev_ble_sync=1,
            todev_set_mnet_cfg_req=dev_net_pb2.SetMnetCfgReq(
                cfg=dev_net_pb2.MnetCfg(
                    type=dev_net_pb2.NET_TYPE_WIFI,
                    inet_enable=new_4g_status,
                    mnet_enable=new_4g_status
                )
            )
        )
        self.send_order_msg_net(build)
        print(
            f"Send command - set 4G (on/off status). newWifiStatus={new_4g_status}")

    def set_device_wifi_enable_status(self, new_wifi_status: bool):
        build = dev_net_pb2.DevNet(
            todev_ble_sync=1,
            todev_wifi_configuration=dev_net_pb2.DrvWifiSet(
                config_param=4,
                wifi_enable=new_wifi_status
            )
        )
        self.send_order_msg_net(build)
        print(
            f"szNetwork: Send command - set network (on/off status). newWifiStatus={new_wifi_status}")


    def wifi_connectinfo_update(self, device_name: str, is_binary: bool):
        print(
            f"Send command - get Wifi connection information.wifiConnectinfoUpdate().deviceName={device_name}.isBinary={is_binary}")
        if is_binary:
            build = dev_net_pb2.DevNet(
                todev_ble_sync=1, todev_wifi_msg_upload=dev_net_pb2.DrvWifiUpload(wifi_msg_upload=1))
            print("Send command - get Wifi connection information")
            print("Send command - get Wifi connection information")
            self.send_order_msg_net(build)
            return
        self.wifi_connectinfo_update2()

    def wifi_connectinfo_update2(self):
        hash_map = {"getMsgCmd": 1}
        self.post_custom_data(self.get_json_string(68, hash_map))

    def get_record_wifi_list(self, is_binary: bool):
        print(f"getRecordWifiList().isBinary={is_binary}")
        if is_binary:
            build = dev_net_pb2.DevNet(
                todev_ble_sync=1, todev_wifi_list_upload=dev_net_pb2.DrvWifiList())
            print("Send command - get memorized WiFi list upload command")
            self.send_order_msg_net(build)
            return
        self.get_record_wifi_list2()

    def get_record_wifi_list2(self):
        self.post_custom_data(self.get_json_string(69))


    def close_clear_connect_current_wifi(self, ssid: str, status: int, is_binary: bool):
        if is_binary:
            build = dev_net_pb2.DevNet(
                todev_ble_sync=1,
                todev_wifi_configuration=dev_net_pb2.DrvWifiSet(
                    config_param=status,
                    confssid=ssid
                )
            )
            print(
                f"Send command - set network (disconnect, direct connect, forget, no operation reconnect) operation command (downlink ssid={ssid}, status={status})")
            self.send_order_msg_net(build)
            return
        self.close_clear_connect_current_wifi2(ssid, status)

    def close_clear_connect_current_wifi2(self, ssid: str, get_msg_cmd: int):
        data = {
            "ssid": ssid,
            "getMsgCmd": get_msg_cmd
        }
        self.post_custom_data(
            self.get_json_string(bleOrderCmd.close_clear_connect_current_wifi, data).encode())


    # === sendOrderMsg_Driver ===

    def send_order_msg_driver(self, driver):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_EMBED_DRIVER,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            driver=driver)

        return luba_msg.SerializeToString()

    def set_knife_height(self, height: int):
        print(f"Send knife height height={height}")
        build = mctrl_driver_pb2.MctlDriver(todev_knife_hight_set=mctrl_driver_pb2.DrvKnifeHeight(knife_height=height))
        print(f"Send command--Knife motor height setting height={height}")
        self.send_order_msg_driver(build)

    def set_speed(self, speed: float):
        print(f"{self.get_device_name()} set speed, {speed}")
        build = mctrl_driver_pb2.MctlDriver(bidire_speed_read_set=mctrl_driver_pb2.DrvSrSpeed(speed=speed, rw=1))
        print(f"Send command--Speed setting speed={speed}")
        self.send_order_msg_driver(build)

    def syn_nav_star_point_data(self, sat_system: int):
        build = mctrl_driver_pb2.MctlDriver(rtk_sys_mask_query=mctrl_driver_pb2.rtk_sys_mask_query_t(sat_system=sat_system))
        print(f"Send command--Navigation satellite frequency point synchronization={sat_system}")
        self.send_order_msg_driver(build)

    def set_nav_star_point(self, cmd_req: str):
        build = mctrl_driver_pb2.MctlDriver(rtk_cfg_req=mctrl_driver_pb2.rtk_cfg_req_t(cmd_req=cmd_req, cmd_length=len(cmd_req) - 1))
        print(f"Send command--Navigation satellite frequency point setting={cmd_req}")
        print(f"Navigation satellite setting, Send command--Navigation satellite frequency point setting={cmd_req}")
        self.send_order_msg_driver(build)

    def get_speed(self):
        build = mctrl_driver_pb2.MctlDriver(bidire_speed_read_set=mctrl_driver_pb2.DrvSrSpeed(rw=0))
        print("Send command--Get speed value")
        self.send_order_msg_driver(build)

    def operate_on_device(self, main_ctrl: int, cut_knife_ctrl: int, cut_knife_height: int, max_run_speed: float):
        build = mctrl_driver_pb2.MctlDriver(mow_ctrl_by_hand=mctrl_driver_pb2.DrvMowCtrlByHand(main_ctrl=main_ctrl, cut_knife_ctrl=cut_knife_ctrl, cut_knife_height=cut_knife_height, max_run_speed=max_run_speed))
        print(f"Send command--Manual mowing command, main_ctrl:{main_ctrl}, cut_knife_ctrl:{cut_knife_ctrl}, cut_knife_height:{cut_knife_height}, max_run_speed:{max_run_speed}")
        self.send_order_msg_driver(build)

    def send_control(self, linear_speed: int, angular_speed: int):
        print(f"Control command print, linearSpeed={linear_speed} // angularSpeed={angular_speed}")
        self.send_order_msg_driver(mctrl_driver_pb2.MctlDriver(todev_devmotion_ctrl=mctrl_driver_pb2.DrvMotionCtrl(set_linear_speed=linear_speed, set_angular_speed=angular_speed)))
    # === sendOrderMsg_Sys ===
    
    def send_order_msg_sys(self, sys):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_EMBED_SYS,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            sys=sys
        )

        return luba_msg.SerializeToString()

    def reset_system(self):
        build = mctrl_sys_pb2.MctlSys(todev_reset_system=1)
        print("Send command - send factory reset")
        self.send_order_msg_sys(build)

    def get_device_product_model(self):
        self.send_order_msg_sys(mctrl_sys_pb2.MctlSys(device_product_type_info=mctrl_sys_pb2.device_product_type_info_t()), 12, True)

    def read_and_set_sidelight(self, is_sidelight: bool, operate: int):
        if is_sidelight:
            build = mctrl_sys_pb2.TimeCtrlLight(operate=operate, enable=0, action=0, start_hour=0, start_min=0, end_hour=0, end_min=0)
        else:
            build = mctrl_sys_pb2.TimeCtrlLight(operate=operate, enable=1, action=0, start_hour=0, start_min=0, end_hour=0, end_min=0)
        print(f"Send read and write sidelight command is_sidelight:{is_sidelight}, operate:{operate}")
        build2 = mctrl_sys_pb2.MctlSys(todev_time_ctrl_light=build)
        print(f"Send command - send read and write sidelight command is_sidelight:{is_sidelight}, operate:{operate}, timeCtrlLight:{build}")
        self.send_order_msg_sys(build2)

    def test_tool_order_to_sys(self, sub_cmd: int, param_id: int, param_value: List[int]):
        build = mctrl_sys_pb2.mCtrlSimulationCmdData(sub_cmd=sub_cmd, param_id=param_id, param_value=param_value)
        print(f"Send tool test command: subCmd={sub_cmd}, param_id:{param_id}, param_value={param_value}")
        build2 = mctrl_sys_pb2.MctlSys(simulation_cmd=build)
        print(f"Send tool test command: subCmd={sub_cmd}, param_id:{param_id}, param_value={param_value}")
        self.send_order_msg_sys(build2)

    def read_and_set_rt_k_paring_code(self, op: int, cgf: str):
        print(f"Send read and write base station configuration quality op:{op}, cgf:{cgf}")
        self.send_order_msg_sys(mctrl_sys_pb2.MctlSys(todev_lora_cfg_req=mctrl_sys_pb2.LoraCfgReq(op=op, cfg=cgf)))

    def allpowerfull_rw_adapter_x3(self, id: int, context: int, rw: int) -> None:
        build = mctrl_nav_pb2.MctlNav(
            nav_sys_param_cmd=mctrl_nav_pb2.nav_sys_param_msg(
                id=id, context=context, rw=rw
            )
        )
        print(f"Send command--9 general read and write command id={id}, context={context}, rw={rw}")
        self.send_order_msg_nav(build)
        
    def allpowerfull_rw(self, id: int, context: int, rw: int):
        if (id == 6 or id == 3 or id == 7) and DeviceType.is_luba_pro(self.get_device_name()):
            self.allpowerfull_rw_adapter_x3(id, context, rw)
            return
        build = mctrl_sys_pb2.MctlSys(bidire_comm_cmd=mctrl_sys_pb2.SysCommCmd(id=id, context=context, rw=rw))
        print(f"Send command - 9 general read and write command id={id}, context={context}, rw={rw}")
        if id == 5:
            # This logic doesnt make snese, but its what they had so..
            self.send_order_msg_sys(build)
            return
        self.send_order_msg_sys(build)        
        
    def factory_test_order(self, test_id: int, test_duration: int, expect: str):
        new_builder = mctrl_sys_pb2.mow_to_app_qctools_info_t.Builder()
        print(f"Factory tool print, expect={expect}")
        if not expect:
            build = new_builder.set_type_value(test_id).set_time_of_duration(test_duration).build()
        else:
            try:
                json_array = json.loads(expect)
                z2 = True
                for i in range(len(json_array)):
                    new_builder2 = mctrl_sys_pb2.QCAppTestExcept.Builder()
                    json_object = json_array[i]
                    if "except_type" in json_object:
                        string = json_object["except_type"]
                        if "conditions" in json_object:
                            json_array2 = json_object["conditions"]
                            for i2 in range(len(json_array2)):
                                json_object2 = json_array2[i2]
                                new_builder3 = mctrl_sys_pb2.QCAppTestConditions.Builder()
                                if "cond_type" in json_object2:
                                    new_builder3.set_cond_type(json_object2["cond_type"])
                                else:
                                    z2 = False
                                if "value" in json_object2:
                                    obj = json_object2["value"]
                                    if string == "int":
                                        new_builder3.set_int_val(int(obj))
                                    elif string == "float":
                                        new_builder3.set_float_val(float(obj))
                                    elif string == "double":
                                        new_builder3.set_double_val(float(obj))
                                    elif string == "string":
                                        new_builder3.set_string_val(str(obj))
                                    else:
                                        z2 = False
                                    new_builder2.add_conditions(new_builder3)
                                else:
                                    z2 = False
                        new_builder2.set_except_type(string)
                        new_builder.add_except(new_builder2)
                        new_builder2.clear()
                z = z2
            except json.JSONDecodeError:
                z = False
            if z:
                build = new_builder.set_type_value(test_id).set_time_of_duration(test_duration).build()
            else:
                build = new_builder.set_type_value(test_id).set_time_of_duration(test_duration).build()
        print(f"Factory tool print, mow_to_app_qctools_info_t={build.except_count}, mow_to_app_qctools_info_t22={build.except_list}")
        build2 = mctrl_sys_pb2.MctlSys(mow_to_app_qctools_info=build)
        print(f"Send command - factory tool test command testId={test_id}, testDuration={test_duration}", "Factory tool print222", True)
        self.send_order_msg_sys(build2)

    def send_sys_set_date_time(self):
        calendar = datetime.now()
        i = calendar.year
        i2 = calendar.month
        i3 = calendar.day
        i4 = calendar.isoweekday()
        i5 = calendar.hour
        i6 = calendar.minute
        i7 = calendar.second
        i8 = calendar.utcoffset().total_seconds() // 60 if calendar.utcoffset() else 0
        i9 = 1 if calendar.dst() else 0
        print(f"Print time zone, time zone={i8}, daylight saving time={i9} week={i4}")
        build = mctrl_sys_pb2.MctlSys(todev_data_time=mctrl_sys_pb2.SysSetDateTime(year=i, month=i2, date=i3, week=i4, hours=i5, minutes=i6, seconds=i7, time_zone=i8, daylight=i9))
        print(f"Send command - synchronize time zone={i8}, daylight saving time={i9} week={i4}, day:{i3}, month:{i2}, hours:{i5}, minutes:{i6}, seconds:{i7}, year={i}", "Time synchronization", True)
        self.send_order_msg_sys(build)

    def get_device_version_info(self):
        self.send_order_msg_sys(mctrl_sys_pb2.MctlSys(todev_get_dev_fw_info=1))
        
    # === sendOrderMsg_Nav ===
    
    def send_order_msg_nav(self, build):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            net=build)

        return luba_msg.SerializeToString()

      
    # === sendOrderMsg_Media ===
    
    def send_order_msg_media(self, mul):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_MUL,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.SOC_MODULE_MULTIMEDIA,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            mul=mul)

        return luba_msg.SerializeToString()

    def set_car_volume(self, volume: int):
        self.send_order_msg_media(luba_mul_pb2.SocMul(set_audio=luba_mul_pb2.MulSetAudio(au_switch=volume)))

    def set_car_voice_language(self, language_type: int):
        self.send_order_msg_media(luba_mul_pb2.SocMul(set_audio=luba_mul_pb2.MulSetAudio(au_language_value=language_type)))

    def set_car_wiper(self, round: int):
        self.send_order_msg_media(luba_mul_pb2.SocMul(set_wiper=luba_mul_pb2.MulSetWiper(round=round)))

    # === sendOrderMsg_Ota ===
    
    def send_order_msg_ota(self, ota):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MsgCmdType.MSG_CMD_TYPE_EMBED_OTA,
            sender=luba_msg_pb2.MsgDevice.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.MsgDevice.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MsgAttr.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            ota=ota)
        
        return luba_msg.SerializeToString()
    

    def get_device_ota_info(self, log_type: int):
        todev_get_info_req = mctrl_ota_pb2.MctlOta(
            todev_get_info_req=mctrl_ota_pb2.getInfoReq(
                type=mctrl_ota_pb2.IT_OTA
            )
        )

        print("===Send command to get upgrade details===logType:" + str(log_type))
        return self.send_order_msg_ota(todev_get_info_req)

    def get_device_info_new(self):
        """New device call for OTA upgrade information."""
        todev_get_info_req = mctrl_ota_pb2.MctlOta(
            todev_get_info_req=mctrl_ota_pb2.getInfoReq(
                type=mctrl_ota_pb2.IT_BASE
            )
        )
        print("Send to get OTA upgrade information", "Get device information")
        return self.send_order_msg_ota(todev_get_info_req)