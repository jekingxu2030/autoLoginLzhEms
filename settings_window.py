import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import datetime


class SettingsWindow:

    def __init__(self, root, callback=None, stop_event=None):
        self.root = root
        self.root.title("系统配置")
        self.root.geometry("400x500")
        self.root.resizable(False, False)

        # 配置文件路径
        self.config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.json"
        )
        self.callback = callback
        self.config_data = self.load_config()

        # 创建UI
        self.create_widgets()

    def load_config(self):
        """加载配置文件"""
        try:
            # 打开配置文件
            with open(self.config_path, "r", encoding="utf-8") as f:
                # 返回配置文件内容
                return json.load(f)
        except Exception as e:
            # 弹出错误提示框
            messagebox.showerror("错误", f"加载配置文件失败: {str(e)}")
            # 返回默认配置
            return {
                "account": {"username": "WC001", "password": "123456789"},
                "timing": {"load_wait_time": 5, "loop_interval": 60, "dingtalk_times": 5},
                "encryption": {"ws_token_key": ""}
            }

    def on_exit(self):
        """退出整个应用程序"""
        if messagebox.askyesno("确认退出", "确定要退出整个程序吗?"):
            # 销毁窗口
            self.root.destroy()
            self.stop_event.set()    # ① 通知主线程停止
            # 退出程序
            import sys
            sys.exit(0)

    def save_config(self):
        """保存配置文件"""
        try:
            # 验证密钥长度
            key = self.key_entry.get().strip()
            if len(key) != 32:
                messagebox.showerror("错误", "加密密钥必须是16字节长度!")
                return

            # 更新配置数据
            self.config_data["account"]["username"] = self.username_entry.get().strip()
            self.config_data["account"]["password"] = self.password_entry.get().strip()
            self.config_data["timing"]["load_wait_time"] = int(
                self.load_wait_entry.get()
            )
            self.config_data["timing"]["loop_interval"] = int(
                self.loop_interval_entry.get()
            )
            self.config_data["encryption"]["ws_token_key"] = key
            self.config_data["timing"]["dingtalk_times"] = int(
                self.dingtalk_times_entry.get()
            )

            # 保存到文件
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=4)

            messagebox.showinfo("成功", "配置保存成功!")
            # 更新调试输出
            debug_text = f"保存成功: {datetime.datetime.now()}"
            self.debug_label.config(text=debug_text[:20])
            # 保存后不关闭窗口
            # 调用回调函数通知主程序配置已更新
            if self.callback:
                self.callback()
            # # 保存后不关闭窗口
        # self.root.destroy()
        except ValueError:
            messagebox.showerror("错误", "时间设置必须是整数!")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置文件失败: {str(e)}")

    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 账户设置
        ttk.Label(main_frame, text="账户设置", font=("微软雅黑", 12, "bold")).grid(
            row=0, column=0, columnspan=2, pady=( 5), sticky="w"
        )

        ttk.Label(main_frame, text="用户名:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        self.username_entry = ttk.Entry(main_frame, width=30)
        self.username_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.username_entry.insert(0, self.config_data["account"]["username"])

        ttk.Label(main_frame, text="密码:").grid(
            row=2, column=0, padx=5, pady=2, sticky="e"
        )
        self.password_entry = ttk.Entry(main_frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.password_entry.insert(0, self.config_data["account"]["password"])

        # 时间设置
        ttk.Label(main_frame, text="时间设置", font=("微软雅黑", 12, "bold")).grid(
            row=3, column=0, columnspan=3, pady=( 5), sticky="w"
        )

        ttk.Label(main_frame, text="加载等待时间(秒):", width=30).grid(
            row=4, column=0, padx=5, pady=(5), sticky="e"
        )
        self.load_wait_entry = ttk.Entry(main_frame, width=10)
        self.load_wait_entry.grid(row=4, column=1, padx=5, pady=(5), sticky="w")
        self.load_wait_entry.insert(
            0, str(self.config_data["timing"]["load_wait_time"])
        )

        ttk.Label(main_frame, text="循环执行间隔(秒):").grid(
            row=5, column=0, padx=5, pady=5, sticky="e"
        )    
        self.loop_interval_entry = ttk.Entry(main_frame, width=10)
        self.loop_interval_entry.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        self.loop_interval_entry.insert(
            0, str(self.config_data["timing"]["loop_interval"])
        )

        # 加密设置
        ttk.Label(main_frame, text="加密设置", font=("微软雅黑", 12, "bold")).grid(
            row=6, column=0, columnspan=2, pady=10, sticky="w"
        )

        ttk.Label(main_frame, text="WS Token密钥(16字节):").grid(
            row=7, column=0, padx=5, pady=5, sticky="e"
        )
        self.key_entry = ttk.Entry(main_frame, width=40)
        self.key_entry.grid(row=7, column=1, padx=5, pady=5, sticky="w")
        self.key_entry.insert(0, self.config_data["encryption"]["ws_token_key"])
        ttk.Label(main_frame, text="(必须是16位字符)", font=("微软雅黑", 8)).grid(
            row=8, column=1, padx=5, pady=(5), sticky="w"
        )

        # 钉钉推送时间间隔设置
        ttk.Label(main_frame, text="钉钉推送设置", font=('微软雅黑', 12, 'bold')).grid(
            row=9, column=0, columnspan=2, pady=(15), sticky='w'
        )
        ttk.Label(main_frame, text="推送间隔次数(次):").grid(
            row=10, column=0, padx=5, pady=5, sticky='e'
        )
        self.dingtalk_times_entry = ttk.Entry(main_frame, width=10)
        self.dingtalk_times_entry.grid(row=10, column=1, padx=5, pady=5, sticky='w')
        self.dingtalk_times_entry.insert(
            0, str(self.config_data['timing']['dingtalk_times'])
        )

        # 1. 让按钮框居中
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=11, column=0, columnspan=2, pady=10, sticky="ew")

        # 2. 让父容器列可扩展
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # 3. 按钮横向排列并自动居中（用 pack + expand）
        ttk.Button(button_frame, text="保存并开始运行", command=self.save_config).pack(
            side=tk.LEFT, padx=10
        )
        # 关闭窗口按钮
        ttk.Button(button_frame, text="关闭窗口", command=self.root.destroy).pack(
            side=tk.LEFT, padx=10
        )

        # 退出程序按钮
        ttk.Button(button_frame, text="退出程序", command=self.on_exit).pack(
            side=tk.LEFT, padx=10
        )
        ttk.Button(button_frame, text="关闭程序", command=self.root.destroy).pack(
            side=tk.LEFT, padx=10
        )

        # 调试输出
        ttk.Label(main_frame, text="调试输出:").grid(row=14, column=0, padx=5, pady=(5), sticky="w")
        self.debug_label = ttk.Label(main_frame, text="", width=50)
        self.debug_label.grid(row=14, column=1, padx=5, pady=(1,5), sticky="w")

    def run_settings_window():
        root = tk.Tk()
        app = SettingsWindow(root, callback=on_config_saved, stop_event=stop_event)
        root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = SettingsWindow(root)
    root.mainloop()
