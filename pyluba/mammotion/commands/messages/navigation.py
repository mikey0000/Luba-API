# === sendOrderMsg_Nav ===
import logging
from typing import List, Dict
import json
import time

from pyluba.data.model import GenerateRouteInformation
from pyluba.data.model.plan import Plan
from pyluba.data.model.region_data import RegionData
from pyluba.mammotion.commands.abstract_message import AbstractMessage
from pyluba.proto import luba_msg_pb2, mctrl_nav_pb2
from pyluba.proto.mctrl_nav import MctlNav, NavPlanJobSet

logger = logging.getLogger(__name__)

class MessageNavigation(AbstractMessage):

    @staticmethod
    def send_order_msg_nav(build):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MSG_CMD_TYPE_NAV,
            sender=luba_msg_pb2.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.DEV_MAINCTL,
            msgattr=luba_msg_pb2.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            net=build)

        return luba_msg.SerializeToString()

    def allpowerfull_rw_adapter_x3(self, id: int, context: int, rw: int) -> bytes:
        build = mctrl_nav_pb2.MctlNav(
            nav_sys_param_cmd=mctrl_nav_pb2.nav_sys_param_msg(
                id=id, context=context, rw=rw
            )
        )
        logger.debug(
            f"Send command--9 general read and write command id={id}, context={context}, rw={rw}")
        return self.send_order_msg_nav(build)

    def along_border(self):
        build: mctrl_nav_pb2.MctlNav = mctrl_nav_pb2.MctlNav(todev_edgecmd=1)
        logger.debug("Send command--along the edge command")
        return self.send_order_msg_nav(build)

    def start_draw_border(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=0,
                type=0
            )
        )
        logger.debug("Send command--Start drawing boundary command")
        return self.send_order_msg_nav(build)

    def enter_dumping_status(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=14,
                type=12
            )
        )
        logger.debug("Send command--Enter grass collection status")
        return self.send_order_msg_nav(build)

    def add_dump_point(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=0,
                type=12
            )
        )
        logger.debug("Send command--Add grass collection point")
        return self.send_order_msg_nav(build)

    def revoke_dump_point(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=6,
                type=12
            )
        )
        logger.debug("Send command--Revoke grass collection point")
        return self.send_order_msg_nav(build)

    def exit_dumping_status(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=1,
                type=12
            )
        )
        logger.debug("Send command--Exit grass collection setting status")
        return self.send_order_msg_nav(build)

    def out_drop_dumping_add(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=15,
                type=12
            )
        )
        logger.debug("Send command--Complete external grass collection point marking operation")
        return self.send_order_msg_nav(build)

    def recover_dumping(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=12,
                type=12
            )
        )
        logger.debug("Send command--Recover grass collection operation")
        return self.send_order_msg_nav(build)

    def start_draw_barrier(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=0,
                type=1
            )
        )
        logger.debug("Sending command - Draw obstacle command")
        return self.send_order_msg_nav(build)

    def start_erase(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=4,
                type=0
            )
        )
        logger.debug("Sending command - Start erase command - Bluetooth")
        return self.send_order_msg_nav(build)

    def end_erase(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=5,
                type=0
            )
        )
        logger.debug("Sending command - End erase command")
        return self.send_order_msg_nav(build)

    def cancel_erase(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=7,
                type=0
            )
        )
        logger.debug("Sending command - Cancel erase command")
        return self.send_order_msg_nav(build)

    def start_channel_line(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=0,
                type=2
            )
        )
        logger.debug("Sending command - Start drawing channel line command")
        return self.send_order_msg_nav(build)

    def save_task(self):
        build = mctrl_nav_pb2.MctlNav(todev_save_task=1)
        logger.debug("Sending command - Save task command")
        return self.send_order_msg_nav(build)

    def set_edit_boundary(self, action: int):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=action,
                type=0
            )
        )
        logger.debug(f"Sending secondary editing command action={action}")
        return self.send_order_msg_nav(build)

    def set_data_synchronization(self, type: int):
        logger.debug(
            f"Sync data ==================== Sending ============ Restore command: {type}")
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1,
                action=12,
                type=type
            )
        )
        logger.debug("Sync data ==================== Sending ============ Restore command")
        return self.send_order_msg_nav(build)

    def send_plan(self, plan_bean: Plan) -> bytes:
        build = MctlNav(
            todev_planjob_set=NavPlanJobSet(
                pver=plan_bean.pver,
                sub_cmd=plan_bean.sub_cmd,
                area=plan_bean.area,
                work_time=plan_bean.work_time,
                version=plan_bean.version,
                id=plan_bean.id,
                user_id=plan_bean.user_id,
                device_id=plan_bean.device_id,
                plan_id=plan_bean.plan_id,
                task_id=plan_bean.task_id,
                job_id=plan_bean.job_id,
                start_time=plan_bean.start_time,
                end_time=plan_bean.end_time,
                week=plan_bean.week,
                knife_height=plan_bean.knife_height,
                model=plan_bean.model,
                edge_mode=plan_bean.edge_mode,
                required_time=plan_bean.required_time,
                route_angle=plan_bean.route_angle,
                route_model=plan_bean.route_model,
                route_spacing=plan_bean.route_spacing,
                ultrasonic_barrier=plan_bean.ultrasonic_barrier,
                total_plan_num=plan_bean.total_plan_num,
                plan_index=plan_bean.plan_index,
                result=plan_bean.result,
                speed=plan_bean.speed,
                task_name=plan_bean.task_name,
                job_name=plan_bean.job_name,
                zone_hashs=plan_bean.zone_hashs,
                reserved=plan_bean.reserved
            )
        )
        logger.debug(f"Send command--Send job plan command planBean={plan_bean}")
        return self.send_order_msg_nav(build)

    def send_plan2(self, plan_bean: Plan) -> bytes:
        build = mctrl_nav_pb2.NavPlanJobSet(
            pver=plan_bean.pver,
            sub_cmd=plan_bean.sub_cmd,
            area=plan_bean.area,
            device_id=plan_bean.device_id,
            work_time=plan_bean.work_time,
            version=plan_bean.version,
            id=plan_bean.id,
            user_id=plan_bean.user_id,
            device_id=plan_bean.device_id,
            plan_id=plan_bean.plan_id,
            task_id=plan_bean.task_id,
            job_id=plan_bean.job_id,
            start_time=plan_bean.start_time,
            end_time=plan_bean.end_time,
            week=plan_bean.week,
            knife_height=plan_bean.knife_height,
            model=plan_bean.model,
            edge_mode=plan_bean.edge_mode,
            required_time=plan_bean.required_time,
            route_angle=plan_bean.route_angle,
            route_model=plan_bean.route_model,
            route_spacing=plan_bean.route_spacing,
            ultrasonic_barrier=plan_bean.ultrasonic_barrier,
            total_plan_num=plan_bean.total_plan_num,
            plan_index=plan_bean.plan_index,
            result=plan_bean.result,
            speed=plan_bean.speed,
            task_name=plan_bean.task_name,
            job_name=plan_bean.job_name,
            zone_hashs=plan_bean.zone_hashs,
            reserved=plan_bean.reserved
        )
        logger.debug(f"Send read job plan command planBean={plan_bean}")
        return self.send_order_msg_nav(mctrl_nav_pb2.MctlNav(todev_planjob_set=build))

    def send_schedule(self, plan_bean: Plan) -> bytes:
        build = mctrl_nav_pb2.NavPlanJobSet(
            pver=plan_bean.pver,
            sub_cmd=plan_bean.sub_cmd,
            area=plan_bean.area,
            device_id=plan_bean.device_id,
            work_time=plan_bean.work_time,
            version=plan_bean.version,
            id=plan_bean.id,
            user_id=plan_bean.user_id,
            plan_id=plan_bean.plan_id,
            task_id=plan_bean.task_id,
            job_id=plan_bean.job_id,
            start_time=plan_bean.start_time,
            end_time=plan_bean.end_time,
            week=plan_bean.week,
            knife_height=plan_bean.knife_height,
            model=plan_bean.model,
            edge_mode=plan_bean.edge_mode,
            required_time=plan_bean.required_time,
            route_angle=plan_bean.route_angle,
            route_model=plan_bean.route_model,
            route_spacing=plan_bean.route_spacing,
            ultrasonic_barrier=plan_bean.ultrasonic_barrier,
            total_plan_num=plan_bean.total_plan_num,
            plan_index=plan_bean.plan_index,
            result=plan_bean.result,
            speed=plan_bean.speed,
            task_name=plan_bean.task_name,
            job_name=plan_bean.job_name,
            zone_hashs=plan_bean.zone_hashs,
            reserved=plan_bean.reserved,
            weeks=plan_bean.weeks,
            start_date=plan_bean.start_date,
            trigger_type=plan_bean.job_type,
            day=plan_bean.interval_days,
            toward_included_angle=plan_bean.demond_angle,
            toward_mode=0
        )
        logger.debug(f"Send read job plan command planBean={plan_bean}")
        return self.send_order_msg_nav(mctrl_nav_pb2.MctlNav(todev_planjob_set=build))

    def single_schedule(self, plan_id: str) -> None:
        return self.send_order_msg_nav(mctrl_nav_pb2.MctlNav(
            plan_task_execute=mctrl_nav_pb2.nav_plan_task_execute(
                sub_cmd=1,
                id=plan_id
            )
        ))

    def read_plan(self, sub_cmd: int, plan_index: int, log_type: int) -> bytes:
        build = mctrl_nav_pb2.MctlNav(
            todev_planjob_set=mctrl_nav_pb2.NavPlanJobSet(
                sub_cmd=sub_cmd,
                plan_index=plan_index
            )
        )
        logger.debug(f"Send read job plan command cmd={
              sub_cmd} PlanIndex = {plan_index},logType={log_type}")
        return self.send_order_msg_nav(build)

    def delete_plan(self, sub_cmd: int, plan_id: str) -> bytes:
        build = mctrl_nav_pb2.MctlNav(
            todev_planjob_set=mctrl_nav_pb2.NavPlanJobSet(
                sub_cmd=sub_cmd,
                plan_id=plan_id
            )
        )
        logger.debug(
            f"Send command--Send delete job plan command cmd={sub_cmd} planId = {plan_id}")
        return self.send_order_msg_nav(build)

    def set_plan_unable_time(self, sub_cmd: int, device_id: str, unable_end_time: str, unable_start_time: str) -> bytes:
        build = mctrl_nav_pb2.NavUnableTimeSet(
            sub_cmd=sub_cmd,
            device_id=device_id,
            unable_end_time=unable_end_time,
            result=0,
            reserved="0",
            unable_start_time=unable_start_time
        )
        logger.debug(f"{self.get_device_name()} Set forbidden time===={build}")
        return self.send_order_msg_nav(
            mctrl_nav_pb2.MctlNav(todev_unable_time_set=build))

    def read_plan_unable_time(self, sub_cmd: int) -> bytes:
        build = mctrl_nav_pb2.NavUnableTimeSet(sub_cmd=sub_cmd)
        build2 = mctrl_nav_pb2.MctlNav(todev_unable_time_set=build)
        logger.debug(f"Send command--Read plan time{sub_cmd}")
        return self.send_order_msg_nav(build2)

    def query_job_history(self) -> bytes:
        return self.send_order_msg_nav(mctrl_nav_pb2.MctlNav(
            todev_work_report_update_cmd=mctrl_nav_pb2.WorkReportUpdateCmd(
                sub_cmd=1
            )
        ))

    def request_job_history(self, num: int) -> bytes:
        return self.send_order_msg_nav(mctrl_nav_pb2.MctlNav(
            todev_work_report_cmd=mctrl_nav_pb2.WorkReportCmdData(
                sub_cmd=1,
                get_info_num=num
            )
        ))

    def leave_dock(self):
        build = mctrl_nav_pb2.MctlNav(todev_one_touch_leave_pile=1)
        logger.debug("Send command--One-click automatic undocking")
        return self.send_order_msg_nav(build)

    def get_all_boundary_hash_list(self, sub_cmd: int):
        build = mctrl_nav_pb2.MctlNav(
            todev_gethash=mctrl_nav_pb2.NavGetHashList(pver=1, subCmd=sub_cmd)
        )
        logger.debug(f"Area loading=====================:Get area hash list++Bluetooth:{
              sub_cmd}")
        return self.send_order_msg_nav(build)

    def get_hash_response(self, total_frame: int, current_frame: int):
        build = mctrl_nav_pb2.MctlNav(
            todev_gethash=mctrl_nav_pb2.NavGetHashList(
                pver=1, subCmd=2, currentFrame=current_frame, totalFrame=total_frame)
        )
        logger.debug(f"Send command--208 Response hash list command totalFrame={
              total_frame},currentFrame={current_frame}")
        return self.send_order_msg_nav(build)

    def synchronize_hash_data(self, hash_num: int):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1, action=8, dataHash=hash_num, subCmd=1)
        )
        logger.debug(f"Send command--209,hash synchronize area data hash:{hash}")
        return self.send_order_msg_nav(build)

    def get_area_to_be_transferred(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1, action=8, subCmd=1, type=3)
        )
        logger.debug("Send command--Get transfer area before charging pile")
        return self.send_order_msg_nav(build)

    def get_regional_data(self, regional_data_bean: RegionData):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1, action=regional_data_bean.action, type=regional_data_bean.type,
                dataHash=regional_data_bean.hash, total_frame=regional_data_bean.total_frame,
                current_frame=regional_data_bean.current_frame, subCmd=2
            )
        )
        logger.debug("Area loading=====================:Response area data")
        return self.send_order_msg_nav(build)

    def indoor_simulation(self, flag: int):
        build = mctrl_nav_pb2.MctlNav(
            simulation_cmd=mctrl_nav_pb2.SimulationCmdData(subCmd=flag)
        )
        logger.debug(f"Send command--Send indoor simulation command flag={flag}")
        return self.send_order_msg_nav(build)

    def send_tools_order(self, id: int, values: List[int]):
        build = mctrl_nav_pb2.MctlNav(
            simulation_cmd=mctrl_nav_pb2.SimulationCmdData(
                subCmd=2, param_id=id, param_value=values)
        )
        logger.debug(f"Send command--Send tool command id={id},values={values}")
        return self.send_order_msg_nav(build)

    def end_draw_border(self, type: int):
        if type == -1:
            return
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1, action=1, type=type)
        )
        logger.debug(
            f"Send command--End drawing boundary, obstacle, channel command type={type}")
        return self.send_order_msg_nav(build)

    def cancel_current_record(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1, action=7, sub_cmd=0)
        )
        logger.debug("Send command--Cancel current recording (boundary, obstacle)")
        return self.send_order_msg_nav(build)

    def delete_map_elements(self, type: int, hash_num: int):
        if type == -1:
            return
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1, action=6, type=type, hash=hash_num)
        )
        logger.debug(
            f"Send command--Delete boundary or obstacle or channel command type={type},hash={hash}")
        return self.send_order_msg_nav(build)

    def delete_charge_point(self):
        logger.debug("Delete charging pile")
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1, action=6, type=5)
        )
        logger.debug("Send command--Delete charging pile location and reset")
        return self.send_order_msg_nav(build)

    def confirm_base_station(self):
        logger.debug("Reset base station")
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1, action=2, type=7)
        )
        logger.debug("Send command--Confirm no modification to base station")
        return self.send_order_msg_nav(build)

    def delete_all(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_get_commondata=mctrl_nav_pb2.NavGetCommData(
                pver=1, action=6, type=6)
        )
        logger.debug("Send command--Clear job data")
        return self.send_order_msg_nav(build)

    def generate_route_information(self, generate_route_information: GenerateRouteInformation):
        logger.debug(f"Generate route data source:{generate_route_information}")
        build = mctrl_nav_pb2.NavReqCoverPath(
            pver=1, sub_cmd=0, zone_hashs=generate_route_information.one_hashs,
            job_mode=generate_route_information.job_mode, edge_mode=generate_route_information.edge_mode,
            knife_height=generate_route_information.knife_height, speed=generate_route_information.speed,
            ultra_wave=generate_route_information.ultra_wave, channel_width=generate_route_information.channel_width,
            channel_mode=generate_route_information.channel_mode, toward=generate_route_information.toward,
            toward_included_angle=generate_route_information.toward_included_angle,
            toward_mode=generate_route_information.toward_mode, reserved=generate_route_information.path_order
        )
        logger.debug(f"{self.get_device_name()}Generate route====={build}")
        logger.debug(f"Send command--Generate route information generateRouteInformation={
              generate_route_information}")
        return self.send_order_msg_nav(mctrl_nav_pb2.MctlNav(bidire_reqconver_path=build))

    def modify_generate_route_information(self, generate_route_information: GenerateRouteInformation):
        logger.debug(f"Generate route data source: {generate_route_information}")
        build = mctrl_nav_pb2.NavReqCoverPath(
            pver=1,
            sub_cmd=3,
            zone_hashs=generate_route_information.one_hashs,
            job_mode=generate_route_information.job_mode,
            edge_mode=generate_route_information.edge_mode,
            knife_height=generate_route_information.knife_height,
            speed=generate_route_information.speed,
            ultra_wave=generate_route_information.ultra_wave,
            channel_width=generate_route_information.channel_width,
            channel_mode=generate_route_information.channel_mode,
            toward=generate_route_information.toward,
            reserved=generate_route_information.path_order
        )
        logger.debug(f"{self.get_device_name()} Generate route ===== {build}")
        logger.debug(f"Send command -- Modify route parameters generate_route_information={
              generate_route_information}")
        return self.send_order_msg_nav(mctrl_nav_pb2.MctlNav(bidire_reqconver_path=build))

    def end_generate_route_information(self):
        build = mctrl_nav_pb2.NavReqCoverPath(pver=1, sub_cmd=9)
        logger.debug(f"{self.get_device_name()} Generate route ===== {build}")
        build2 = mctrl_nav_pb2.MctlNav(bidire_reqconver_path=build)
        logger.debug(
            "Send command -- End generating route information generate_route_information=")
        return self.send_order_msg_nav(build2)

    def query_generate_route_information(self):
        build = mctrl_nav_pb2.NavReqCoverPath(pver=1, sub_cmd=2)
        logger.debug(f"{self.get_device_name(
        )} Send command -- Get route configuration information generate_route_information={build}")
        build2 = mctrl_nav_pb2.MctlNav(bidire_reqconver_path=build)
        return self.send_order_msg_nav(build2)

    def get_line_info(self, current_hash: int) -> bytes:
        logger.debug(f"Sending==========Get route command: {current_hash}")
        build = mctrl_nav_pb2.MctlNav(
            todev_zigzag_ack=mctrl_nav_pb2.NavUploadZigZagResultAck(
                pver=1,
                currentHash=current_hash,
                subCmd=0
            )
        )
        logger.debug(f"Sending command--Get route data corresponding to hash={current_hash}")
        return self.send_order_msg_nav(build)

    def get_line_info_list(self, list: List[int], transaction_id: int) -> bytes:
        logger.debug(f"Sending==========Get route command: {list}")
        build = mctrl_nav_pb2.MctlNav(
            app_request_cover_paths=mctrl_nav_pb2.app_request_cover_paths_t(
                pver=1,
                hash_list=list,
                transaction_id=transaction_id,
                sub_cmd=0
            )
        )
        logger.debug(f"Sending command--Get route data corresponding to hash={list}")
        return self.send_order_msg_nav(build)

    def start_job(self) -> bytes:
        logger.debug("Sending==========Start job command")
        build = mctrl_nav_pb2.MctlNav(
            todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(
                type=1,
                action=1,
                result=0
            )
        )
        logger.debug("Sending command--Start job")
        return self.send_order_msg_nav(build)

    def cancel_return_to_dock(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(type=1, action=12, result=0))
        logger.debug("Send command - Cancel return to charge")
        return self.send_order_msg_nav(build)

    def cancel_job(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(type=1, action=4, result=0))
        logger.debug("Send command - End job")
        return self.send_order_msg_nav(build)

    def return_to_dock(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(type=1, action=5, result=0))
        logger.debug("Send command - Return to charge command")
        return self.send_order_msg_nav(build)

    def pause_execute_task(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(type=1, action=2, result=0))
        logger.debug("Send command - Pause command")
        return self.send_order_msg_nav(build)

    def re_charge_test(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(type=1, action=10, result=0))
        logger.debug("Send command - Return to charge test command")
        return self.send_order_msg_nav(build)

    def fast_aotu_test(self, action: int):
        build = mctrl_nav_pb2.MctlNav(
            todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(type=1, action=action, result=0))
        logger.debug("Send command - One-click automation test")
        return self.send_order_msg_nav(build)

    def resume_execute_task(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(type=1, action=3, result=0))
        logger.debug("Send command - Cancel pause command")
        return self.send_order_msg_nav(build)

    def break_point_continue(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(type=1, action=7, result=0))
        logger.debug("Send command - Continue from breakpoint")
        return self.send_order_msg_nav(build)

    def break_point_anywhere_continue(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(type=1, action=9, result=0))
        logger.debug("Send command - Continue from current vehicle position")
        return self.send_order_msg_nav(build)

    def reset_base_station(self):
        build = mctrl_nav_pb2.MctlNav(
            todev_taskctrl=mctrl_nav_pb2.NavTaskCtrl(type=3, action=1, result=0))
        logger.debug("Send command - Reset charging pile, base station position")
        return self.send_order_msg_nav(build)