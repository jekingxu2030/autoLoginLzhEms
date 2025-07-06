import json
import time
from datetime import datetime


class EmsWsMonitor:
    def __init__(self, driver, timeout=15):
        """
        :param driver: selenium 的 WebDriver 实例（用于监听）
        :param timeout: 最大等待秒数
        """
        self.driver = driver
        self.timeout = timeout
        self.start_time = datetime.now()
        self.msg_arrived = False
        self.data_valid = False

    def start(self) -> str:
        """启动监听并判断数据状态"""

        print("[WS] 启动性能日志监听...")
        try:
            while (datetime.now() - self.start_time).total_seconds() < self.timeout:
                logs = self.driver.get_log("performance")
                for entry in logs:
                    try:
                        message = json.loads(entry["message"])["message"]
                        if message["method"] == "Network.webSocketFrameReceived":
                            payload = message["params"]["response"]["payloadData"]

                            if '"func":"rtv"' in payload:
                                self.msg_arrived = True
                                print(f"\n[WS拦截] 收到数据帧: {payload[:80]}...")
                                
                                data = json.loads(payload)
                                rtv_data = data.get("data", [])
                                print(f"\n[WS拦截] 共接收 {len(rtv_data)} 个字段ID")
                                  
                                for item in data.get("data", []):
                                    val = item.get("value")
                                    if val not in ("", None, 87, "87"):
                                        self.data_valid = True
                                        break

                                if self.data_valid:
                                    return "ok"

                    except Exception as e:
                        print(f"[WS监听异常] {e}")
                        return "error"

                time.sleep(0.5)

            # 超时判断
            if not self.msg_arrived:
                return "no_msg"
            elif not self.data_valid:
                return "empty"
            else:
                return "ok"

        except Exception as e:
            print(f"[WS错误] {e}")
            return "no_ws"
