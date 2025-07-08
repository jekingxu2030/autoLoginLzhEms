import json
import time
from datetime import datetime
import asyncio
import websockets
from configparser import ConfigParser
import os


def fetch_menu_once():
    """独立请求一次 menu 数据，并返回提取的 rtv_id 列表或完整 menu"""
    config = ConfigParser()
    config.read("config.ini")

    ws_url = config.get("websocket", "url")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Origin": "http://ems.hy-power.net:8114",
        "X-LocalStorage": (
            f"local-power-station-active-emsid={config.get('localStorage', 'local-power-station-active-emsid')};"
            f"locale={config.get('localStorage', 'locale')};"
            f"timezone={config.get('localStorage', 'timezone')};"
            f"user_id={config.get('localStorage', 'user_id')}"
        ),
        "X-SessionStorage": f"session-power-station-active-emsid={config.get('session_storage', 'session-power-station-active-emsid')}",
    }

    async def fetch():
        try:
            async with websockets.connect(ws_url, extra_headers=headers) as ws:
                await ws.send(json.dumps({"func": "menu"}))
                print("menu订阅发送完成")

                for _ in range(3):  # 最多等待 5 条数据
                    raw = await ws.recv()
                    data = json.loads(raw)

                    if data.get("func") == "menu":
                        print(
                            f"[MENU] 收到 menu 数据，字段数量: {len(data.get('data', {}))}"
                        )
                        # print(f"[MENU]数据: {data[1]}")   #---字典不能切分打印
                        # print(f"[MENU]数据（前10项）: {dict(list(data.items())[:10])}")
                        print(
                            f"[MENU]Data数据的第一层键名: {list(data.get('data', {}).keys())}"
                        )
                        
                     
                        return data.get("data")

                    else:
                        print(f"[MENU] 忽略非 menu 数据: func = {data.get('func')}")

                print("[MENU] 未收到 menu 类型数据")
                return None
        except Exception as e:
            print(f"[MENU] 获取失败: {e}")
            return None

    return asyncio.run(fetch())


class EmsWsMonitor:
    def __init__(self, driver, timeout=15, menu_data=None):
        self.driver = driver
        self.timeout = timeout
        self.start_time = datetime.now()
        self.msg_arrived = False
        self.data_valid = False
        self.menu_data = menu_data  # 保存外部传入的 menu 数据

    def start(self):
        print("[WS] 启动性能日志监听...")
        try:
            if self.menu_data:
                print(f"[WS] 预载 menu 数据，设备种类: {len(self.menu_data)}")

                print(f"[MENU]顶层字段键名: {list(self.menu_data.keys())}")

                menu_cache = self.parse_menu_data(self.menu_data)
                self.menu_cache = menu_cache  # ← 加这一句
                print("[MENU] 缓存字典数据项:", len(menu_cache))  # 总共多少个设备类型
                for device_type, field_list in menu_cache.items():
                    print(
                        f"[MENU] 设备类型: {device_type}，字段数量: {len(field_list)}"
                    )

                    # 保存menu_list数据到文件
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                log_dir = os.path.join(os.path.dirname(__file__), "dataLog")
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f"menu_list_update_{timestamp}.json")
                # with open(log_file, "w", encoding="utf-8") as f:
                #     json.dump(menu_cache, f, ensure_ascii=False, indent=2)
                # print(f"[DEBUG] Menu_list数据已保存到: {log_file}")

                # print(f"\n[WS] 菜单list整理完成:{menu_cache}")
            else:
                print("[WS] 未传入 menu 数据")
        except Exception as e:
            print(f"[WS]Menu数据处理异常: {e}")

        try:
            while (datetime.now() - self.start_time).total_seconds() < self.timeout:
                logs = self.driver.get_log("performance")
                for entry in logs:
                    try:
                        message = json.loads(entry["message"])["message"]
                        if message["method"] == "Network.webSocketFrameReceived":
                            payload = message["params"]["response"]["payloadData"]

                            try:
                                data = json.loads(payload)
                            except:
                                data = {}

                            if data.get("func") == "rtv":
                                self.msg_arrived = True
                                print(f"\n[WS拦截] 收到RTV数据帧: {payload[:20]}...")

                                rtv_data = data.get("data", [])
                                print(f"\n[WS拦截] 共接收 {len(rtv_data)} 个字段ID")

                                for item in rtv_data:
                                    val = item.get("value")
                                    if val not in ("", None, 87, "87"):
                                        self.data_valid = True
                                        break

                                if hasattr(self, "menu_cache"):  # 确保 menu_cache 存在
                                    updated_count = 0
                                    for item in rtv_data:
                                        try:
                                            new_id = int(item["id"])
                                            new_value = item["value"]
                                            updated = False
                                            for (
                                                device_type,
                                                field_list,
                                            ) in self.menu_cache.items():
                                                for entry in field_list:
                                                    if entry["id"] == new_id:
                                                        entry["value"] = new_value
                                                        # print(
                                                        #     f"[更新] 设备类型: {device_type} → ID: {new_id}, Value: {new_value}"
                                                        # )
                                                        updated = True
                                                        updated_count += 1
                                                        break
                                                if updated:
                                                    break
                                        except Exception as e:
                                            print(
                                                f"[更新异常] id={item.get('id')}: {e}"
                                            )
                                    print(f"[RTV] 共更新字段值: {updated_count}")

                                    # 构建导出完整list+data的列表：只导出已更新过 value 的字段（即 value 不为 None）
                                    export_data = []
                                    timestamp = datetime.now().strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    )

                                    for (
                                        device_type,
                                        field_list,
                                    ) in self.menu_cache.items():
                                        for entry in field_list:
                                            if entry.get("value") is not None:
                                                export_item = (
                                                    entry.copy()
                                                )  # 复制原始字段
                                                export_item["device_type"] = device_type
                                                export_item["ts"] = timestamp
                                                export_data.append(export_item)

                                    # 构建保存路径
                                    folder_path = r"F:\360Downloads\BaiduNetdiskDownload\WicToolDemo\getBY_EMS_Data\autoLoginLzhEms\dataLog"
                                    os.makedirs(
                                        folder_path, exist_ok=True
                                    )  # 若目录不存在则创建

                                    file_name = f"rtv_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                                    file_path = os.path.join(folder_path, file_name)

                                    # 保存为 JSON 文件
                                    # with open(file_path, "w", encoding="utf-8") as f:
                                    #     json.dump(
                                    #         export_data, f, ensure_ascii=False, indent=2
                                    #     )
                                    print(f"[RTV] 已保存更新数据到: {file_path}")

                                if self.data_valid:
                                    return "✅ok"

                            elif data.get("func") == "menu":
                                print(f"\n[WS拦截] MENU数据: {payload[:20]}...")

                    except Exception as e:
                        print(f"[WS监听异常] {e}")
                        return "❌error"

                time.sleep(0.5)

            if not self.msg_arrived:
                return "❌no_msg"
            elif not self.data_valid:
                return "❌empty"
            else:
                return "✅ok"

        except Exception as e:
            print(f"[WS错误] {e}")
            return "❌no_ws"

    # 数据合成处理
    def parse_menu_data(self, menu_data):
        """
        解析menu的data字段，返回缓存字典。
        缓存结构：{
            device_type: [
                {
                    "id": ...,
                    "fieldChnName": ...,
                    "fieldEngName": ...,
                    "value": None,
                    "engName": ...（如果存在）
                    "tableName": ...（如果存在）
                }, ...
            ],
            ...
        }
        """
        cache = {}

        for device_type, device_list in menu_data.items():
            cache[device_type] = []
            for device in device_list:
                rtv_list = device.get("rtvList", [])
                for rtv_item in rtv_list:
                    entry = {
                        "id": rtv_item.get("id"),
                        "fieldChnName": rtv_item.get("fieldChnName"),
                        "fieldEngName": rtv_item.get("fieldEngName"),
                        "value": None,
                    }
                    # 只有当字段存在时才加入
                    if "engName" in rtv_item:
                        entry["engName"] = rtv_item["engName"]
                    if "tableName" in rtv_item:
                        entry["tableName"] = rtv_item["tableName"]
                    if "engName" in rtv_item:
                        entry["engName"] = rtv_item["engName"]
                    if "fieldName" in rtv_item:
                        entry["fieldName"] = rtv_item["fieldName"]
                    cache[device_type].append(entry)

        return cache
