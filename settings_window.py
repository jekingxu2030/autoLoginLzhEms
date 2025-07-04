import tkinter as tk
from tkinter import ttk, messagebox
import json, os, datetime
# import tkinter as tk      # 记得已经 import 过就不用再写


class SettingsWindow:
    """系统配置窗口"""

    def __init__(self, root, callback=None, stop_event=None):
        self.root = root
        self.root.title("LZH-EMS_State_Check")
        self.root.geometry("400x500")
        self.root.resizable(False, False)

        # 依赖
        self.callback = callback  # 保存后回调
        self.stop_event = stop_event  # UI 请求停止主线程

        # 配置文件
        self.cfg_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.json"
        )
        self.cfg = self._load_cfg()

        # UI
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    # ------------------------------------------------------------------
    # 加载 / 保存
    # ------------------------------------------------------------------
    def _load_cfg(self):
        try:
            with open(self.cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "account": {"username": "WC001", "password": "123456789"},
                "timing": {
                    "load_wait_time": 5,
                    "loop_interval": 60,
                    "dingtalk_times": 5,
                },
                "encryption": {"ws_token_key": ""},
            }

    def _save_cfg(self):
        try:
            key = self.key_entry.get().strip()
            # if len(key) != 32:
            #     messagebox.showerror("错误", "加密密钥必须是 16 字节（32 个字符）!")
            #     return

            # 更新内存配置
            self.cfg["account"]["username"] = self.user_entry.get().strip()
            self.cfg["account"]["password"] = self.pwd_entry.get().strip()
            self.cfg["timing"]["load_wait_time"] = int(self.wait_entry.get())
            self.cfg["timing"]["loop_interval"] = int(self.loop_entry.get())
            self.cfg["timing"]["dingtalk_times"] = int(self.dt_times_entry.get())
            self.cfg["encryption"]["ws_token_key"] = key

            with open(self.cfg_path, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=4)

            self._log("配置保存成功")#传递到调试标签
            messagebox.showinfo("提示", "配置保存成功!")
            if self.callback: 
                self.callback()  # 唤醒主线程

        except ValueError:
            messagebox.showerror("错误", "时间 / 次数必须为整数!")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
            self._log("保存失败")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        m = ttk.Frame(self.root, padding=20)
        m.pack(fill=tk.BOTH, expand=True)

        # 账户
        ttk.Label(m, text="账户设置", font=("微软雅黑", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(m, text="用户名:").grid(row=1, column=0, sticky="e", pady=3)
        self.user_entry = ttk.Entry(m, width=28)
        self.user_entry.grid(row=1, column=1, sticky="w")
        self.user_entry.insert(0, self.cfg["account"]["username"])

        ttk.Label(m, text="密码:").grid(row=2, column=0, sticky="e", pady=3)
        self.pwd_entry = ttk.Entry(m, width=28, show="*")
        self.pwd_entry.grid(row=2, column=1, sticky="w")
        self.pwd_entry.insert(0, self.cfg["account"]["password"])

        # 时间
        ttk.Label(m, text="时间设置", font=("微软雅黑", 12, "bold")).grid(
            row=3, column=0, columnspan=2, pady=(10, 0), sticky="w"
        )
        ttk.Label(m, text="加载等待(秒):").grid(row=4, column=0, sticky="e", pady=3)
        self.wait_entry = ttk.Entry(m, width=10)
        self.wait_entry.grid(row=4, column=1, sticky="w")
        self.wait_entry.insert(0, self.cfg["timing"]["load_wait_time"])

        ttk.Label(m, text="循环间隔(秒):").grid(row=5, column=0, sticky="e", pady=3)
        self.loop_entry = ttk.Entry(m, width=10)
        self.loop_entry.grid(row=5, column=1, sticky="w")
        self.loop_entry.insert(0, self.cfg["timing"]["loop_interval"])

        # 加密
        ttk.Label(m, text="加密设置", font=("微软雅黑", 12, "bold")).grid(
            row=6, column=0, columnspan=2, pady=(10, 0), sticky="w"
        )
        ttk.Label(m, text="WS Token密钥(32字符):").grid(
            row=7, column=0, sticky="e", pady=3
        )
        self.key_entry = ttk.Entry(m, width=32)
        self.key_entry.grid(row=7, column=1, sticky="w")
        self.key_entry.insert(0, self.cfg["encryption"]["ws_token_key"])

        # 钉钉
        ttk.Label(m, text="钉钉推送", font=("微软雅黑", 12, "bold")).grid(
            row=8, column=0, columnspan=2, pady=(10, 0), sticky="w"
        )
        ttk.Label(m, text="推送间隔次数:").grid(row=9, column=0, sticky="e", pady=3)
        self.dt_times_entry = ttk.Entry(m, width=10)
        self.dt_times_entry.grid(row=9, column=1, sticky="w")
        self.dt_times_entry.insert(0, self.cfg["timing"]["dingtalk_times"])

        # 按钮
        btn = ttk.Frame(m)
        btn.grid(row=10, column=0, columnspan=2, padx=5, pady=15)
        ttk.Button(btn, text="保存并开始运行",  command=self._save_cfg).pack(
            side=tk.LEFT, padx=10, pady=( 5)
        )
        ttk.Button(btn, text="停止执行", command=self._stop).pack(side=tk.LEFT, pady=( 5),padx=10)

        # 日志
        for r in range(0, 13):
         m.rowconfigure(r, weight=1)   # 行 0~9 会被“撑开”
          # ↳ m 是整个主 frame  
        debug_frame = ttk.Frame(m)
        # debug_frame.pack(side="bottom", fill="x")   # 始终贴底、横向铺满
        # debug_frame = ttk.Frame(m)
        debug_frame.grid(row=13, column=0, columnspan=2, sticky="w", padx=2, pady=2)
        ttk.Label(debug_frame, text="调试:").pack(side="left")
        self.log_lbl = tk.Label(
            debug_frame,
            text="",
            width=50,
            anchor="w",
            # relief="solid",
            borderwidth=1,
        )
        self.log_lbl.pack(side="left", padx=2,pady=2)
        self.log_lbl.config(font=("Consolas", 8))  

        m.columnconfigure(1, weight=1)  # 让第二列拉伸

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------
    def _stop(self):
        if messagebox.askyesno("确认", "确定要停止主线程吗?"):
            if self.stop_event:
                self.stop_event.set()
            self._log("已请求停止主线程")

    def _log(self, msg):
        self.log_lbl.config(text=f"{msg}  {datetime.datetime.now():%H:%M:%S}")
    
    # 更新调试标签
    def update_debug_label(self, text):
        # 将传入的文本设置为调试标签的文本
        self.log_lbl.config(text=text)
