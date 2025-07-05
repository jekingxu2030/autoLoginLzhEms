


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
        # 初始化 WebSocket 连接
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
        self._stop_event = threading.Event()  # 停止事件，用于停止线程

    def stop_monitor(self):
        """
        显式停止监控线程和WebSocket连接
        """
        # 停止监控线程
        self.stop()
        # 如果监控线程存在且正在运行，则等待1秒后停止
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        # 如果WebSocket连接存在，则关闭连接
        if self.ws:
            self.ws.close()
        # 打印提示信息
        print("WebSocket 监控已完全停止")

    # ─────────── WebSocket 回调 ───────────
    def _on_message(self, ws, message: str):
        self.msg_arrived = True  # 收到任何消息
        try:
            payload = json.loads(message)
            if payload.get("func") == "rtv":
                for item in payload.get("data", []):
                    v = item.get("value") 
                    print(f"收到数据value: {v}")
                    # 有效值判定：既不为空/None，也不等于 87 或 "87"
                    if v not in ("", None, 87, "87"):
                        self.data_valid = True
                        break
        except json.JSONDecodeError:
            pass
        print(f"收到数据推送: {message[:220]}...")

    def _on_error(self, ws, error):
        # 打印 WebSocket 错误信息
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
        # 设置停止事件
        self._stop_event.set()
        # 如果WebSocket存在，则关闭
        if self.ws:
            self.ws.close()
        # 如果线程存在且正在运行，则等待线程结束
        if self.thread and self.thread.is_alive():
            self.thread.join()
        # 打印WebSocket监听已停止
        print("WebSocket 监听已停止")
