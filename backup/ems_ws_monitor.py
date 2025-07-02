

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

    def __init__(self, ws_url: str, timeout: int = 15):
        if not ws_url:
            raise ValueError("无法获取 WebSocket URL，无法连接")
        self.ws_url = ws_url
        self.timeout = timeout  # 超时时间（秒）
        self.data_received = False  # 收到任何推送后置 True
        self.ws = None
        self.thread = None
        self._stop_event = threading.Event()

    # ───────────────────── WebSocket 事件回调 ──────────────────────
    def _on_message(self, ws, message):
        self.data_received = True  # 标记已收到数据
        print(f"收到数据推送: {message[:120]}...")

    def _on_error(self, ws, error):
        print(f"WebSocket 错误: {error}")

    def _on_close(self, ws, code, msg):
        print(f"WebSocket 关闭: {code}, {msg}")

    def _on_open(self, ws):
        # 定义订阅消息，包括函数名、订阅的股票代码列表和订阅周期
        sub_msg = {"func": "rtv", "ids": self.ids_list, "period": 0}
        # 打印WebSocket已连接，并发送订阅消息
        print("WebSocket 已连接，发送订阅:", sub_msg)
        ws.send(json.dumps(sub_msg))
        # 等待1秒
        time.sleep(3)

    # ────────────────────────── 公开接口 ───────────────────────────
    def start(self) -> bool:
        """
        建立连接 → 订阅 → 监听至超时，返回布尔值表示是否收到了数据推送
        """
        self._stop_event.clear()
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        # 背景线程跑 WebSocket
        self.thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.thread.start()

        # 在主线程等待 timeout 秒，看是否收到数据
        start_t = time.time()
        while not self.data_received and time.time() - start_t < self.timeout:
            time.sleep(0.5)

        self.stop()  # 结束连接
        return self.data_received  # True=正常, False=异常

    def stop(self):
        self._stop_event.set()
        if self.ws:
            self.ws.close()
        if self.thread and self.thread.is_alive():
            self.thread.join()
        print("WebSocket 监听已停止")
