# import tkinter as tk
# from tkinter import ttk, messagebox
# import json
# import os
# import datetime


# class SettingsWindow:

#     def __init__(self, root, callback=None, stop_event=None):
#         self.root = root
#         self.root.title("系统配置")
#         self.root.geometry("400x500")
#         self.root.resizable(False, False)

#         # 配置文件路径
#         self.config_path = os.path.join(
#             os.path.dirname(os.path.abspath(__file__)), "config.json"
#         )
#         self.callback = callback
#         self.config_data = self.load_config()

#         # 创建UI
#         self.create_widgets()
#         self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

#     def load_config(self):
#         """加载配置文件"""
#         try:
#             # 打开配置文件
#             with open(self.config_path, "r", encoding="utf-8") as f:
#                 # 返回配置文件内容
#                 return json.load(f)
#         except Exception as e:
#             # 弹出错误提示框
#             messagebox.showerror("错误", f"加载配置文件失败: {str(e)}")
#             # 返回默认配置
#             return {
#                 "account": {"username": "WC001", "password": "123456789"},
#                 "timing": {"load_wait_time": 5, "loop_interval": 60, "dingtalk_times": 5},
#                 "encryption": {"ws_token_key": ""}
#             }

#     def on_exit(self):
#         """退出整个应用程序"""
#         if messagebox.askyesno("确认退出", "确定要退出整个程序吗?"):
#             self.debug_label.config(text="程序即将退出")
#             if hasattr(self, 'stop_event'):
#                 self.stop_event.set()
#             self.root.destroy()

#     def save_config(self):
#         """保存配置文件"""
#         try:
#             # 验证密钥长度
#             key = self.key_entry.get().strip()
#             if len(key) != 32:
#                 messagebox.showerror("错误", "加密密钥必须是16字节长度!")
#                 return

#             # 更新配置数据
#             self.config_data["account"]["username"] = self.username_entry.get().strip()
#             self.config_data["account"]["password"] = self.password_entry.get().strip()
#             self.config_data["timing"]["load_wait_time"] = int(
#                 self.load_wait_entry.get()
#             )
#             self.config_data["timing"]["loop_interval"] = int(
#                 self.loop_interval_entry.get()
#             )
#             self.config_data["encryption"]["ws_token_key"] = key
#             self.config_data["timing"]["dingtalk_times"] = int(
#                 self.dingtalk_times_entry.get()
#             )

#             # 保存到文件
#             with open(self.config_path, "w", encoding="utf-8") as f:
#                 json.dump(self.config_data, f, ensure_ascii=False, indent=4)

#             messagebox.showinfo("成功", "配置保存成功!")
#             self.debug_label.config(text="配置保存成功")
#             # 更新调试输出
#             debug_text = f"保存成功: {datetime.datetime.now()}"
#             self.debug_label.config(text=debug_text[:20])
#             # 保存后不关闭窗口
#             # 调用回调函数通知主程序配置已更新
#             if self.callback:
#                 self.callback()
#             # # 保存后不关闭窗口
#         # self.root.destroy()
#         except ValueError:
#             messagebox.showerror("错误", "时间设置必须是整数!")
#         except Exception as e:
#             messagebox.showerror("错误", f"保存配置文件失败: {str(e)}")
#             self.debug_label.config(text="配置保存失败")

#     def create_widgets(self):
#         """创建界面组件"""
#         # 创建主框架
#         main_frame = ttk.Frame(self.root, padding="20")
#         main_frame.pack(fill=tk.BOTH, expand=True)

#         # 账户设置
#         ttk.Label(main_frame, text="账户设置", font=("微软雅黑", 12, "bold")).grid(
#             row=0, column=0, columnspan=2, pady=( 5), sticky="w"
#         )

#         ttk.Label(main_frame, text="用户名:").grid(
#             row=1, column=0, padx=5, pady=5, sticky="e"
#         )
#         self.username_entry = ttk.Entry(main_frame, width=30)
#         self.username_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
#         self.username_entry.insert(0, self.config_data["account"]["username"])

#         ttk.Label(main_frame, text="密码:").grid(
#             row=2, column=0, padx=5, pady=2, sticky="e"
#         )
#         self.password_entry = ttk.Entry(main_frame, width=30, show="*")
#         self.password_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
#         self.password_entry.insert(0, self.config_data["account"]["password"])

#         # 时间设置
#         ttk.Label(main_frame, text="时间设置", font=("微软雅黑", 12, "bold")).grid(
#             row=3, column=0, columnspan=3, pady=( 5), sticky="w"
#         )

#         ttk.Label(main_frame, text="加载等待时间(秒):", width=30).grid(
#             row=4, column=0, padx=5, pady=(5), sticky="e"
#         )
#         self.load_wait_entry = ttk.Entry(main_frame, width=10)
#         self.load_wait_entry.grid(row=4, column=1, padx=5, pady=(5), sticky="w")
#         self.load_wait_entry.insert(
#             0, str(self.config_data["timing"]["load_wait_time"])
#         )

#         ttk.Label(main_frame, text="循环执行间隔(秒):").grid(
#             row=5, column=0, padx=5, pady=5, sticky="e"
#         )
#         self.loop_interval_entry = ttk.Entry(main_frame, width=10)
#         self.loop_interval_entry.grid(row=5, column=1, padx=5, pady=5, sticky="w")
#         self.loop_interval_entry.insert(
#             0, str(self.config_data["timing"]["loop_interval"])
#         )

#         # 加密设置
#         ttk.Label(main_frame, text="加密设置", font=("微软雅黑", 12, "bold")).grid(
#             row=6, column=0, columnspan=2, pady=10, sticky="w"
#         )

#         ttk.Label(main_frame, text="WS Token密钥(16字节):").grid(
#             row=7, column=0, padx=5, pady=5, sticky="e"
#         )
#         self.key_entry = ttk.Entry(main_frame, width=40)
#         self.key_entry.grid(row=7, column=1, padx=5, pady=5, sticky="w")
#         self.key_entry.insert(0, self.config_data["encryption"]["ws_token_key"])
#         ttk.Label(main_frame, text="(必须是16位字符)", font=("微软雅黑", 8)).grid(
#             row=8, column=1, padx=5, pady=(5), sticky="w"
#         )

#         # 钉钉推送时间间隔设置
#         ttk.Label(main_frame, text="钉钉推送设置", font=('微软雅黑', 12, 'bold')).grid(
#             row=9, column=0, columnspan=2, pady=(15), sticky='w'
#         )
#         ttk.Label(main_frame, text="推送间隔次数(次):").grid(
#             row=10, column=0, padx=5, pady=5, sticky='e'
#         )
#         self.dingtalk_times_entry = ttk.Entry(main_frame, width=10)
#         self.dingtalk_times_entry.grid(row=10, column=1, padx=5, pady=5, sticky='w')
#         self.dingtalk_times_entry.insert(
#             0, str(self.config_data['timing']['dingtalk_times'])
#         )

#         # 1. 让按钮框居中
#         button_frame = ttk.Frame(main_frame)
#         button_frame.grid(row=11, column=0, columnspan=2, pady=10, sticky="ew")

#         # 2. 让父容器列可扩展
#         main_frame.columnconfigure(0, weight=1)
#         main_frame.columnconfigure(1, weight=1)

#         # 3. 按钮横向排列并自动居中（用 pack + expand）
#         ttk.Button(button_frame, text="保存并开始运行",
#                   command=lambda: [self.save_config(), self.root.withdraw()]).pack(
#             side=tk.LEFT, padx=10
#         )
#         ttk.Button(
#             button_frame,
#             text="最小化窗口",
#             command=lambda: [self.root.iconify()],
#         ).pack(side=tk.LEFT, padx=10)
#         # 退出程序按钮
#         ttk.Button(button_frame, text="退出程序", command=self.on_exit).pack(  #self.stop_event.set()
#             side=tk.LEFT, padx=10
#         )

#         # 调试输出
#         ttk.Label(main_frame, text="调试输出:").grid(row=14, column=0, padx=5, pady=(5), sticky="w")
#         self.debug_label = ttk.Label(main_frame, text="", width=100)
#         self.debug_label.grid(row=14, column=1, padx=5, pady=(5), sticky="w")

#     def run_settings_window():
#         root = tk.Tk()
#         app = SettingsWindow(root, callback=on_config_saved, stop_event=stop_event)
#         root.mainloop()

#     # 更新调试标签
#     def update_debug_label(self, message):
#         # 将调试标签的文本设置为传入的message参数
#         self.debug_label.config(text=message)

# if __name__ == "__main__":
#     root = tk.Tk()
#     app = SettingsWindow(root)
#     root.mainloop()


# ======================================2/0


import tkinter as tk
from tkinter import ttk, messagebox
import json, os, datetime


class SettingsWindow:
    """系统配置窗口"""

    def __init__(self, root, callback=None, stop_event=None):
        self.root = root
        self.root.title("系统配置")
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
            if len(key) != 32:
                messagebox.showerror("错误", "加密密钥必须是 16 字节（32 个字符）!")
                return

            # 更新内存配置
            self.cfg["account"]["username"] = self.user_entry.get().strip()
            self.cfg["account"]["password"] = self.pwd_entry.get().strip()
            self.cfg["timing"]["load_wait_time"] = int(self.wait_entry.get())
            self.cfg["timing"]["loop_interval"] = int(self.loop_entry.get())
            self.cfg["timing"]["dingtalk_times"] = int(self.dt_times_entry.get())
            self.cfg["encryption"]["ws_token_key"] = key

            with open(self.cfg_path, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=4)

            self._log("配置保存成功")
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
        btn.grid(row=10, column=0, columnspan=2, pady=15)
        ttk.Button(btn, text="保存并开始运行", command=self._save_cfg).pack(
            side=tk.LEFT, padx=10
        )
        ttk.Button(btn, text="停止执行", command=self._stop).pack(side=tk.LEFT, padx=10)

        # 日志
        ttk.Label(m, text="调试:").grid(row=11, column=0, sticky="w")
        self.log_lbl = ttk.Label(m, text="", width=32)
        self.log_lbl.grid(row=11, column=1, sticky="w")

        m.columnconfigure(1, weight=1)

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
