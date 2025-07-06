# ==========================优化区分数据状态类==================
# ems_ws_monitor.py
import asyncio
import websocket
import threading
import websockets
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
        # 新增headers配置
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Origin": "http://ems.hy-power.net:8114"
        }
        self.websocket = None
        self.reconnect_count = 0  # 重连计数器
        # 状态标记
        self.ws_connected = False  # 连接是否成功
        self.msg_arrived = False  # 是否收到任何推送
        self.data_valid = False  # 推送中是否含有效 value

        self.ws = None
        self.thread = None
        self._stop_event = threading.Event()  # 停止事件，用于停止线程

    def start(self) -> str:
        """同步启动方法，保持原有调用方式"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            print("开始连接WS")
            return loop.run_until_complete(self._async_start())
        finally:
            loop.close()

    async def _async_start(self):
        """异步实现核心连接逻辑"""
        try:
            # 读取config.ini中的认证信息
            from configparser import ConfigParser
            import os
            config = ConfigParser()
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
            config.read(config_path)
            
            # 构建headers - 参考connection.py的完整配置
            self.headers = {
                "User-Agent": "Mozilla/5.0",
                "Origin": "http://ems.hy-power.net:8114",
                "Cookie": f"sa-token={config.get('cookie', 'sa-token')}",
                "X-LocalStorage": f"local-power-station-active-emsid={config.get('localStorage', 'local-power-station-active-emsid')};locale={config.get('localStorage', 'locale')};timezone={config.get('localStorage', 'timezone')};user_id={config.get('localStorage', 'user_id')}",
                "X-SessionStorage": f"session-power-station-active-emsid={config.get('session_storage', 'session-power-station-active-emsid')}",
                "Connection": "Upgrade",
                "Upgrade": "websocket",
                "Sec-WebSocket-Version": "13",
                "Sec-WebSocket-Key": "x3JJHMbDL1EzLkh9GBhXDw=="
            }
            
            self.websocket = await websockets.connect(
                self.ws_url,
                extra_headers=self.headers,
                ping_interval=60,
                ping_timeout=30,
                close_timeout=5,
                max_queue=20248,
                
            )
            print("连接成功")
            await self._subscribe()

            return await self._listen()
        except Exception as e:
            print(f"WebSocket连接错误: {e}")
            return "no_ws"

    async def _subscribe(self):
        """发送订阅请求"""
        sub_msg = {"func": "rtv", "ids": self.ids_list, "period": 0}
        await self.websocket.send(json.dumps(sub_msg))
        print("发送RTV订阅")

    async def _listen(self):
        """监听消息并判断状态"""
        start_t = time.time()
        print("开始监听消息")
        print(f"监听数据返回等待时间:{ self.timeout}")
        while time.time() - start_t < self.timeout:
            try:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=1)
                self.msg_arrived = True
                try:
                    payload = json.loads(message)
                    print(f"收到数据: {payload}")
                    # 有效值判定：既不为空/None，也不等于 87 或 "87"
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
            except asyncio.TimeoutError:
                continue

        return "no_msg" if self.msg_arrived else "empty"

    def _try_connect(self):
        """
        实际连接逻辑
        """
        self._stop_event.clear()
        print("开始启动WS队列线程")
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            header=self.headers,  # 添加headers
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
        print(f"收到on_message消息: {message}")
        try:
            payload = json.loads(message)
            print(f"收到数据: {payload}")
            # 有效值判定：既不为空/None，也不等于 87 或 "87"
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
