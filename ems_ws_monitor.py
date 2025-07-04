# # ems_ws_monitor.py
# import websocket
# import threading
# import json
# import time


# class EmsWsMonitor:
#     # 固定订阅 ID 列表
#     ids_list = [
#         409001058,
#         409001059,
#         409001060,
#         409001061,
#         409001062,
#         409001063,
#         409001067,
#         409001071,
#         409001075,
#     ]

#     def __init__(self, ws_url: str, timeout: int = 15):
#         if not ws_url:
#             raise ValueError("无法获取 WebSocket URL，无法连接")
#         self.ws_url = ws_url
#         self.timeout = timeout  # 超时时间（秒）
#         self.data_received = False  # 收到任何推送后置 True
#         self.ws = None
#         self.thread = None
#         self._stop_event = threading.Event()

#     # ───────────────────── WebSocket 事件回调 ──────────────────────
#     def _on_message(self, ws, message):
#         self.data_received = True  # 标记已收到数据
#         print(f"收到数据推送: {message[:120]}...")

#     def _on_error(self, ws, error):
#         print(f"WebSocket 错误: {error}")

#     def _on_close(self, ws, code, msg):
#         print(f"WebSocket 关闭: {code}, {msg}")

#     def _on_open(self, ws):
#         # 定义订阅消息，包括函数名、订阅的股票代码列表和订阅周期
#         sub_msg = {"func": "rtv", "ids": self.ids_list, "period": 0}
#         # 打印WebSocket已连接，并发送订阅消息
#         print("WebSocket 已连接，发送订阅:", sub_msg)
#         ws.send(json.dumps(sub_msg))
#         # 等待1秒
#         time.sleep(3)

#     # ────────────────────────── 公开接口 ───────────────────────────
#     def start(self) -> bool:
#         """
#         建立连接 → 订阅 → 监听至超时，返回布尔值表示是否收到了数据推送
#         """
#         self._stop_event.clear()
#         self.ws = websocket.WebSocketApp(
#             self.ws_url,
#             on_open=self._on_open,
#             on_message=self._on_message,
#             on_error=self._on_error,
#             on_close=self._on_close,
#         )
#         # 背景线程跑 WebSocket
#         self.thread = threading.Thread(target=self.ws.run_forever, daemon=True)
#         self.thread.start()

#         # 在主线程等待 timeout 秒，看是否收到数据
#         start_t = time.time()
#         while not self.data_received and time.time() - start_t < self.timeout:
#             time.sleep(0.5)

#         self.stop()  # 结束连接
#         return self.data_received  # True=正常, False=异常

#     def stop(self):
#         self._stop_event.set()
#         if self.ws:
#             self.ws.close()
#         if self.thread and self.thread.is_alive():
#             self.thread.join()
#         print("WebSocket 监听已停止")


# ==========================优化区分数据状态类==================
# ems_ws_monitor.py
import websocket
import threading
import json
import time


class EmsWsMonitor:
    # 固定订阅 ID 列表
    ids_list = [
        409001058,
        409001059,
        409001060,
        409001061,
        409001062,
        409001063,
        409001067,
        409001071,
        409001075,
    ]

    def __init__(self, ws_url: str, timeout: int = 15, poll_interval: float = 0.5):
        if not ws_url:
            raise ValueError("无法获取 WebSocket URL，无法连接")

        self.ws_url = ws_url
        self.timeout = timeout  # 总等待上限（秒）
        self.poll_interval = poll_interval  # 轮询间隔
        # 状态标记
        self.ws_connected = False  # 连接是否成功
        self.msg_arrived = False  # 是否收到任何推送
        self.data_valid = False  # 推送中是否含有效 value

        self.ws = None
        self.thread = None
        self._stop_event = threading.Event()

    def stop_monitor(self):
        """
        显式停止监控线程和WebSocket连接
        """
        self.stop()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        if self.ws:
            self.ws.close()
        print("WebSocket 监控已完全停止")

    # ─────────── WebSocket 回调 ───────────
    def _on_message(self, ws, message: str):
        self.msg_arrived = True  # 收到任何消息
        try:
            payload = json.loads(message)
            if payload.get("func") == "rtv":
                for item in payload.get("data", []):
                    v = item.get("value")
                    # 有效值判定：既不为空/None，也不等于 87 或 "87"
                    if v not in ("", None, 87, "87"):
                        self.data_valid = True
                        break
        except json.JSONDecodeError:
            pass
        print(f"收到数据推送: {message[:120]}...")

    def _on_error(self, ws, error):
        print(f"WebSocket 错误: {error}")

    def _on_close(self, ws, code, msg):
        print(f"WebSocket 关闭: {code}, {msg}")

    def _on_open(self, ws):
        self.ws_connected = True
        sub_msg = {"func": "rtv", "ids": self.ids_list, "period": 0}
        print("WebSocket 已连接，发送订阅:", sub_msg)
        ws.send(json.dumps(sub_msg))

    # ───────────── 主启动接口 ──────────────
    def start(self) -> str:
        """
        建立连接→订阅→监听，返回状态字符串:
        'ok'      : 收到推送且含有效 value
        'empty'   : 收到推送但 value 全为空/默认
        'no_msg'  : 连接成功但超时内无任何推送
        'no_ws'   : WS 连接失败
        """
        self._stop_event.clear()
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        # 后台线程跑 WebSocket
        self.thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.thread.start()

        # 在主线程等待 timeout 秒
        start_t = time.time()
        while (not self.msg_arrived) and (time.time() - start_t < self.timeout):
            time.sleep(self.poll_interval)

        self.stop()

        # 状态判定
        if not self.ws_connected:
            return "no_ws"
        if not self.msg_arrived:
            return "no_msg"
        if not self.data_valid:
            return "empty"
        return "ok"

    def stop(self):
        self._stop_event.set()
        if self.ws:
            self.ws.close()
        if self.thread and self.thread.is_alive():
            self.thread.join()
        print("WebSocket 监听已停止")
