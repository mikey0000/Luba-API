# === sendOrderMsg_Net  ===
import json
import time
from typing import Dict
from pyluba.aliyun.tmp_constant import tmp_constant
from pyluba.mammotion.commands.messages.navigation import MessageNavigation
from pyluba.proto import dev_net_pb2, luba_msg_pb2
from pyluba.utility.constant.device_constant import bleOrderCmd


class MessageNetwork:
    messageNavigation: MessageNavigation = MessageNavigation()

    def send_order_msg_net(self, build):
        luba_msg = luba_msg_pb2.LubaMsg(
            msgtype=luba_msg_pb2.MSG_CMD_TYPE_ESP,
            sender=luba_msg_pb2.DEV_MOBILEAPP,
            rcver=luba_msg_pb2.DEV_COMM_ESP,
            msgattr=luba_msg_pb2.MSG_ATTR_REQ,
            seqs=1,
            version=1,
            subtype=1,
            net=build)

        return luba_msg.SerializeToString()

    def get_4g_module_info(self):
        build = dev_net_pb2.DevNet(
            todev_get_mnet_cfg_req=dev_net_pb2.DevNet().todev_get_mnet_cfg_req)
        print("Send command -- Get device 4G network module information")
        return self.send_order_msg_net(build)

    def get_4g_info(self):
        build = dev_net_pb2.DevNet(
            TodevMnetInfoReq=dev_net_pb2.DevNet().TodevMnetInfoReq)
        print("Send command -- Get device 4G network information")
        return self.send_order_msg_net(build)

    def set_zmq_enable(self):
        build = dev_net_pb2.DevNet(
            todev_set_dds2_zmq=dev_net_pb2.DrvDebugDdsZmq(
                is_enable=True,
                rx_topic_name="perception_post_result",
                tx_zmq_url="tcp://0.0.0.0:5555"
            )
        )
        print("Send command -- Set vision ZMQ to enable")
        return self.send_order_msg_net(build)

    def set_iot_setting(self, iot_conctrl_type: dev_net_pb2.iot_conctrl_type):
        build = dev_net_pb2.DevNet(TodevSetIotOfflineReq=iot_conctrl_type)
        print("Send command -- Device re-online")
        return self.send_order_msg_net(build)

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
        return self.send_order_msg_net(dev_net_pb2.DevNet(
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
        return self.send_order_msg_net(dev_net_pb2.DevNet(
            todev_ble_sync=1, todev_uploadfile_req=build))

    def get_device_log_info(self, biz_id: str, type: int, log_url: str) -> None:
        """Get device log info (bluetooth only)."""
        return self.send_order_msg_net(
            dev_net_pb2.DevNet(
                todev_ble_sync=1,
                todev_req_log_info=dev_net_pb2.DrvUploadFileReq(
                    biz_id=biz_id,
                    type=type,
                    url=log_url,
                    num=0,
                    user_id=""  # TODO supply user id
                )
            )
        )

    def cancel_log_update(self, biz_id: str):
        """Cancel log update (bluetooth only)."""
        return self.send_order_msg_net(dev_net_pb2.DevNet(
            todev_log_data_cancel=dev_net_pb2.DrvUploadFileCancel(biz_id=biz_id)))

    def get_device_network_info(self):
        build = dev_net_pb2.DevNet(
            todev_networkinfo_req=dev_net_pb2.GetNetworkInfoReq(req_ids=1))
        print("Send command - get device network information")
        return self.send_order_msg_net(build)

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

        print(
            f"Send command - set 4G (on/off status). newWifiStatus={new_4g_status}")
        return self.send_order_msg_net(build)

    def set_device_wifi_enable_status(self, new_wifi_status: bool):
        build = dev_net_pb2.DevNet(
            todev_ble_sync=1,
            todev_wifi_configuration=dev_net_pb2.DrvWifiSet(
                config_param=4,
                wifi_enable=new_wifi_status
            )
        )
        print(
            f"szNetwork: Send command - set network (on/off status). newWifiStatus={new_wifi_status}")
        return self.send_order_msg_net(build)

    def wifi_connectinfo_update(self, device_name: str, is_binary: bool):
        print(
            f"Send command - get Wifi connection information.wifiConnectinfoUpdate().deviceName={device_name}.isBinary={is_binary}")
        if is_binary:
            build = dev_net_pb2.DevNet(
                todev_ble_sync=1, todev_wifi_msg_upload=dev_net_pb2.DrvWifiUpload(wifi_msg_upload=1))
            print("Send command - get Wifi connection information")
            print("Send command - get Wifi connection information")
            return self.send_order_msg_net(build)
        self.wifi_connectinfo_update2()

    def wifi_connectinfo_update2(self):
        hash_map = {"getMsgCmd": 1}
        self.messageNavigation.post_custom_data(self.get_json_string(
            68, hash_map))  # ToDo: Fix this

    def get_record_wifi_list(self, is_binary: bool):
        print(f"getRecordWifiList().isBinary={is_binary}")
        if is_binary:
            build = dev_net_pb2.DevNet(
                todev_ble_sync=1, todev_wifi_list_upload=dev_net_pb2.DrvWifiList())
            print("Send command - get memorized WiFi list upload command")
            return self.send_order_msg_net(build)
        self.get_record_wifi_list2()

    def get_record_wifi_list2(self):
        self.messageNavigation.post_custom_data(
            self.get_json_string(69))  # ToDo: Fix this

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
            return self.send_order_msg_net(build)
        self.close_clear_connect_current_wifi2(ssid, status)

    def close_clear_connect_current_wifi2(self, ssid: str, get_msg_cmd: int):
        data = {
            "ssid": ssid,
            "getMsgCmd": get_msg_cmd
        }
        self.messageNavigation.post_custom_data(
            # ToDo: Fix this
            self.get_json_string(bleOrderCmd.close_clear_connect_current_wifi, data).encode())

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
