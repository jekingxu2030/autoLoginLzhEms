from asyncio import sleep
import json
import os
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
from settings_window import SettingsWindow
from dingtalk_notify import send_dingtalk_msg
from email_sender_wy import send_email
from selenium import webdriver
import time
import json
from selenium import webdriver
from ems_ws_monitor import EmsWsMonitor, fetch_menu_once

from datetime import datetime
import gc  # 引入垃圾回收模块

# 将WebSocket URL写入config.ini文件
import configparser

# from ems_ws_monitor import EmsWsInterceptor

config = configparser.ConfigParser()

# === 路径 ===
try:
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
except Exception as e:
    print(f"无法确定配置文件路径: {e}")
    config_path = "config.json"  # 默认路径作为回退
JS_SAVE_DIR = "./downloaded_js"
os.makedirs(JS_SAVE_DIR, exist_ok=True)

# 初始化config变量
config = None

# 加载配置文件
try:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    print("错误：配置文件config.json不存在")
    config = None
except json.JSONDecodeError:
    print("错误：配置文件格式不正确，无法解析JSON")
    config = None
except Exception as e:
    print(f"加载配置文件时发生错误: {e}")
    config = None

# === 状态 ===
stop_event = threading.Event()
running_event = threading.Event()


# === 全局变量 ===
driver = None
settings_window = None
stop_event = threading.Event()
config_ready = threading.Event()
# ng.support@baiyiled.nl


def thread_safe_update_debug_label(text):
    # 自动清理日志，当日志行数超过1000行时删除最早的100行
    if (
        hasattr(settings_window, "log_lbl")
        and settings_window.log_lbl.cget("text").count("\n") > 5000
    ):
        current_text = settings_window.log_lbl.cget("text")
        settings_window.log_lbl.config(text="\n".join(current_text.split("\n")[100:]))
    settings_window.log_lbl.after(0, lambda: settings_window.update_debug_label(text))


def set_config_value(filename, section, key, value):
    """
    写入或更新配置文件中的指定值
    :param filename: 配置文件名（如 config.ini）
    :param section: 区段名（如 websocket）
    :param key: 键名（如 url）
    :param value: 键值（如 ws://xxx）
    """
    try:
        config = configparser.ConfigParser()
        # 如果文件存在就读取
        if os.path.exists(filename):
            config.read(filename)
        # 如果没有这个 section 就添加
        if not config.has_section(section):
            config.add_section(section)
        # 设置键值
        config.set(section, key, value)
        # 写入文件
        with open(filename, "w") as configfile:
            config.write(configfile)
        print(f"✅ 写入成功：[{section}] {key} = {value}")  
    except Exception as e:
        print(f"Error writing to config file: {e}")

def get_ws_url(driver):
    # 获取浏览器性能日志
    logs = driver.get_log("performance")
    # 遍历日志
    for entry in logs:
        # 将日志中的message字段转换为json格式
        message = json.loads(entry["message"])["message"]
        # 判断日志中的method字段是否为Network.webSocketCreated
        if message["method"] == "Network.webSocketCreated":
            ws_url = message["params"]["url"]
            # print("✅ 捕获到WebSocket URL:", ws_url)

            # 读取ini并写入配置文件
            set_config_value("config.ini", "websocket", "url", ws_url)
            thread_safe_update_debug_label(
                f"✅ 获取到的 WebSocket 完整地址：{ws_url[30]}"
            )
            return ws_url
    return None


# =================保存cookie、stroge、seection方法
def save_browser_cache_to_config(driver):
    # 保存 Cookies
    for cookie in driver.get_cookies():
        key = str(cookie["name"])
        value = str(cookie["value"])
        set_config_value("config.ini", "cookie", key, value)
        print(f"保存cookie: {cookie['name']} = {cookie['value']}")
    # 保存 localStorage
    local_storage = driver.execute_script(
        """
        let items = {};
        for (let i = 0; i < localStorage.length; i++) {
            let k = localStorage.key(i);
            items[k] = localStorage.getItem(k);
        }
        return items;
    """
    )
    for key, value in local_storage.items():
        set_config_value("config.ini", "localStorage", key, value)
        # print(f"保存localStorage: {key} = {value}")

    # 保存 sessionStorage
    session_storage = driver.execute_script(
        """
        let items = {};
        for (let i = 0; i < sessionStorage.length; i++) {
            let k = sessionStorage.key(i);
            items[k] = sessionStorage.getItem(k);
        }
        return items;
    """
    )
    for key, value in session_storage.items():
        set_config_value("config.ini", "sessionStorage", key, value)
        # print(f"保存sessionStorage: {key} = {value}")


# ==============主线程2.0=======================
# === 主执行函数（登录 + 探测） ===
def login(driver, username, password, load_wait_time):

    driver.get("http://ems.hy-power.net:8114/login")
    thread_safe_update_debug_label("请求网页中...")
    time.sleep(load_wait_time + 10)

    # 设置emsId
    driver.execute_script(
        "localStorage.setItem('local-power-station-active-emsId', 'E6F7D5412A20');"
    )
    time.sleep(load_wait_time)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "canvas")))
    canvas = driver.find_element(By.ID, "canvas")
    verification_code = canvas.get_attribute("verificationcode")
    print("\n✅[验证码] =", verification_code)

    driver.find_element(By.ID, "form_item_username").clear()
    driver.find_element(By.ID, "form_item_username").send_keys(username)
    driver.find_element(By.ID, "form_item_password").clear()
    driver.find_element(By.ID, "form_item_password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, 'input[placeholder="请输入验证码"]').clear()
    driver.find_element(By.CSS_SELECTOR, 'input[placeholder="请输入验证码"]').send_keys(
        verification_code
    )

    time.sleep(load_wait_time + 2)
    WebDriverWait(driver, 10).until(  # 算3秒平均消耗
        EC.element_to_be_clickable((By.CSS_SELECTOR, "form.login-form button"))
    ).click()
    print("\n✅提交了登录表单")

    time.sleep(load_wait_time + 5)
    thread_safe_update_debug_label("登录成功，开始探测内容...")
    # 稍微晚点读取cock
    save_browser_cache_to_config(driver)
  
    ws_url = get_ws_url(driver)  #保持WS字套

def main_logic():
    try:
        # 检查配置是否加载成功
        if config is None:
            print("错误：配置文件加载失败，无法继续执行")
            return
        # 移除原有的config加载代码
        # global config
        # with open(config_path, "r", encoding="utf-8") as f:
        #     config = json.load(f)

        username = config["account"]["username"]
        password = config["account"]["password"]
        load_wait_time = config["timing"]["load_wait_time"]  # 第一个时间
        loop_interval = config["timing"]["loop_interval"]  # 第二个时间
        dingtalk_times = config["timing"]["dingtalk_times"]  # 第三个时间
        # email_times = config["timing"]["email_times"]  #第四个时间
        # email_interval = config["timing"]["email_interval"]  #第五个时间

        global driver
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        driver = webdriver.Chrome(options=options)

        # 登录
        login(driver, username, password, load_wait_time)
        last_login_time = time.time()  # 记录初始登录时间
        time.sleep(load_wait_time + 10)

        # 状态计数变量
        same_error_count = 0
        intervalCounts = 0
        total_cycle_count = 0
        checkCounts = 0

        # 记录开始时间
        start_time = time.time()
        # 在主程序启动时调用
        menu_data = fetch_menu_once()
        # 记录结束时间
        end_time = time.time()
        # 计算耗时（秒）
        elapsed_time1 = end_time - start_time

        while not stop_event.is_set():
            current_time = time.time()

            # 检查是否超过23小时(82800秒)未重新登录
            if current_time - last_login_time >= 23 * 3600:
                #  if current_time - last_login_time >= 23 * 3600:
                print("🔄 已超过23小时，准备重新登录...")
                thread_safe_update_debug_label(f"🔄登录已超过23小时，准备重新登录...")
                # login(driver, username, password, load_wait_time)
                restart_browser(username, password, load_wait_time)  # 
                time.sleep(load_wait_time*2+10)
                last_login_time = current_time  # 更新登录时间

            total_cycle_count += 1

            WebDriverWait(driver, 20).until(  # 算3秒
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            driver.execute_script("window.scrollBy(0, 10);")
            driver.execute_script("window.dispatchEvent(new Event('mousemove'))")
            time.sleep(load_wait_time + 5)

            # ws_url = get_ws_url(driver)
            # 记录开始时间
            start_time = time.time()
            # 原代码包含多余的config参数，已注释
            # ws_monitor = EmsWsMonitor(
            #     driver, timeout=load_wait_time + 15, menu_data=menu_data, config=config
            # )
            # 修改后移除config参数
            ws_monitor = EmsWsMonitor(
                driver, timeout=load_wait_time + 15, menu_data=menu_data
            )
            status = ws_monitor.start()

            # 记录结束时间
            end_time = time.time()
            # 计算耗时（秒）
            elapsed_time2 = end_time - start_time
            print("WS检测状态：", status)
            print(
                f"\nload_wait_time={load_wait_time} , loop_interval={loop_interval},dingtalk_times={dingtalk_times},intervalCounts={intervalCounts},same_error_count={same_error_count}"
            )

            if status == "✅ok":
                same_error_count = 0  # 打断异常，重置异常计数  在连续错误三次或三次后连续错误会一直保持大于3，等待正常逻状态下归零

                # 打印正常状态推送间隔
                normal_push_interval = (
                    (63 + (load_wait_time * 14)) + elapsed_time1 + elapsed_time2
                ) * (max(1,(dingtalk_times * 24) - intervalCounts))

                if intervalCounts >= dingtalk_times * 24:
                    Content = (
                        f"Event: BY-P01-EMS_StatusCheck\n"
                        f"State: Normal!\n"
                        f"CheckUrl: {driver.current_url}\n"
                        f"Message:✅网站正常，收到实时新数据！\n"
                        f"WebSiteState: Accessible！\n"
                        f"time：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_dingtalk_msg(Content)
                    send_email(
                        [
                            "wicpower2023@gmail.com",
                            "531556397@qq.com",
                            "marcin.lee@wic-power.com",
                            "ng.support@baiyiled.nl",
                        ],
                        "【EMS Events】",
                        f"《提示!》\n\n尊敬的用户您好！您的215P01项目EMS后台系统数据“正常” ，请您放心运行!谢谢!\nCheckUrl: {driver.current_url}\n\n\n检测时间：{datetime.now()}",
                        from_addr="jekingxu@163.com",
                    )
                    intervalCounts = 0
                    driver.refresh()  # 刷新网页
                else:
                    print(
                        f"✅ 当前为【正常状态】,距离下次推送间隔约 {normal_push_interval} 秒 ≈ {normal_push_interval / 60:.1f} 分钟"
                    )
                    intervalCounts += 1

            elif status in ["❌empty", "❌no_msg", "❌no_ws", "❌error"]:
                same_error_count += 1
                # 根据状态自适应输出网站状态描述
                if status == "❌empty":
                    web_state_desc = "网站访问正常，但数据返回为空"
                elif status == "❌no_msg":
                    web_state_desc = "WebSocket连接正常，但无有效数据"
                elif status == "❌no_ws":
                    web_state_desc = "⚠️ 无法建立 WebSocket 连接"
                elif status == "❌error":
                    web_state_desc = "❌ 发生未知错误，页面可能无法访问"
                else:
                    web_state_desc = "❓ 不明状态异常"
                errocontent = (
                    f"Event: BY-P01-EMS_StatusCheck\n"
                    f"State: Alarm!\n"
                    f"CheckUrl: {driver.current_url}\n"
                    f"Message:网站状态异常[{status}]，请检查！\n"
                    f"WebSiteState: {web_state_desc}\n"
                    f"time：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

                # 持续异常推送间隔
                error_push_interval = (
                    ((63 + (load_wait_time * 14)) * (loop_interval - same_error_count))
                    + elapsed_time1
                    + elapsed_time2
                ) * (max(1, loop_interval - same_error_count))

                if same_error_count == loop_interval:
                    # 首次异常状态推送间隔
                    error_frist_push_interval = (
                        (63 + (load_wait_time * 14)) + elapsed_time1 + elapsed_time2
                    ) * (
                        max(1, loop_interval - same_error_count)
                    )  # 错误推送也需要等待设定的次数减去相同错误推送次数，避免错误推送间隔过短

                    send_dingtalk_msg(errocontent)
                    send_email(
                        [
                            "wicpower2023@gmail.com",
                            "531556397@qq.com",
                            "marcin.lee@wic-power.com",
                            #"ng.support@baiyiled.nl",
                        ],
                        "【EMS Events】",
                        f"《警告!》\n\n尊敬的用户您好！我们检测到您的215P01项目EMS后台系统出现异常状态：{status}。请您尽快检查和处理!谢谢!\nCheckUrl: {driver.current_url}\n\n\n事件时间：{datetime.now()}",
                        from_addr="jekingxu@163.com",
                    )
                    # same_error_count += 1
                    intervalCounts = 0
                    print(
                        f"❗ 当前为【异常状态: {status}】，距离下轮首错推送时间：{error_frist_push_interval / 60:.1f} 分钟"
                    )
                elif same_error_count > loop_interval:  # 错误连续后时间延长

                    if intervalCounts >= dingtalk_times:  # 延长异常推送间隔
                        send_dingtalk_msg(errocontent)
                        send_email(
                            [
                                "wicpower2023@gmail.com",
                                "531556397@qq.com",
                                "marcin.lee@wic-power.com" "ng.support@baiyiled.nl",
                            ],
                            "【EMS Events】",
                            f"《警告!》\n\n尊敬的用户您好！我们检测到您的215P01项目EMS后台系统持续异常[{status}]。请您尽快检查和处理!谢谢!\nCheckUrl: {driver.current_url}\n\n\n事件时间：{datetime.now()}",
                            from_addr="jekingxu@163.com",
                        )
                        intervalCounts = 0  # 超过三次连续错误后又连续间隔错误次数后归零
                        driver.refresh()  # 刷新网页
                        print(
                            f"❗ 当前为【异常状态: {status}】，距离下一次连续错误推送约 {error_push_interval} 秒 ≈ {error_push_interval / 60:.1f} 分钟"
                        )
                    else:
                        intervalCounts += 1
                        print(f"第{same_error_count}次异常状态，错误次数>0>错误间隔次数<推送间隔")
                else:
                    intervalCounts += 1  #跳过每次都加1
                    print(f"第{same_error_count}次异常状态，错误次数>0<错误间隔次数")

            # 清理缓存与内存
            gc.collect()

            time.sleep(load_wait_time)

            time.sleep(load_wait_time)
            checkCounts += 1
            print(f"\n已经检测第{checkCounts}轮")

            # 定期重启浏览器防止资源泄漏
            if total_cycle_count % 10000 == 0:
                print("🔁 达到1000次检测，准备重启浏览器...")
                try:
                    restart_browser(
                        username, password, load_wait_time + 10
                    )  # 算3秒平均消耗
                    time.sleep(load_wait_time + 5)
                except Exception as e:
                    print(f"🔁 浏览器重启失败: {e}")
                    thread_safe_update_debug_label(f"❌浏览器重启失败: {e}")

                    # 这里要重新执行登录操作（填写用户名、密码、验证码等）
            else:
                print(f"\n已循环{total_cycle_count}次")
    except FileNotFoundError:
        print("错误：配置文件config.json不存在")
        return
    except json.JSONDecodeError:
        print("错误：配置文件格式不正确，无法解析JSON")
        return
    except KeyError as e:
        print(f"错误：配置文件缺少必要的键: {e}")
        return
    except Exception as e:
        print("主线程逻辑异常:", e)
        thread_safe_update_debug_label(f"❌主逻辑异常" + str(e))
        print(f"加载配置文件时发生错误: {e}")
        return
    finally:
        if driver:
            try:
                thread_safe_update_debug_label(f"❌线程退出,正在关闭浏览器...")
                print("⚠️线程退出,正在关闭浏览器")
                driver.quit()
                time.sleep(12)
                if hasattr(driver, "service") and driver.service.process:
                    driver.service.process.terminate()
            except Exception as e:
                print(f"关闭浏览器时出错: {e}")
                thread_safe_update_debug_label(f"❌关闭浏览器时出错: {e}")


# ==============================================
# 重启函数
def restart_browser(username, password, load_wait_time):
    global driver
    try:
        driver.quit()
        time.sleep(5)
    except Exception:
        pass

    gc.collect()
    kill_existing_processes()
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(options=options)
    login(driver, username, password, load_wait_time)
    time.sleep(load_wait_time + load_wait_time + 5)


# ==============================================

# === 设置窗口线程 ===
def run_settings():
    global settings_window
    root = tk.Tk()

    def on_closing():
        # /*******  88517a0e-ce2f-486d-b6d6-1ecd6e20a7f5  *******/
        stop_event.set()
        running_event.clear()
        if driver:
            try:
                driver.quit()
                time.sleep(2)  # 增加等待时间
                if hasattr(driver, "service") and driver.service.process:
                    driver.service.process.kill()  # 使用更强制的方式终止进程
            except Exception as e:
                print(f"关闭浏览器时出错: {e}")
                import os

                os.system("taskkill /f /im chrome.exe")  # 强制终止所有chrome进程
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    settings_window = SettingsWindow(
        root, callback=start_main_logic, stop_event=stop_event
    )
    root.mainloop()


# === 回调触发主逻辑 ===
def start_main_logic():
    # 如果running_event没有设置，则启动主线程
    if not running_event.is_set():
        # 创建一个线程，目标函数为main_logic，设置为守护线程
        logic_thread = threading.Thread(target=main_logic, daemon=True)
        logic_thread.start()
        running_event.set()
        print("🚀 主线程已启动")
        thread_safe_update_debug_label("🚀主线程已启动")


def kill_existing_processes():
    """终止所有与自己相同的Chrome进程"""
    try:
        import psutil

        current_pid = os.getpid()
        for proc in psutil.process_iter(["pid", "name"]):
            if proc.info["name"] == "chrome.exe" and proc.info["pid"] != current_pid:
                try:
                    proc.kill()
                    print(f"✅ 已终止Chrome进程: PID {proc.info['pid']}")
                except Exception as e:
                    print(f"❌ 终止Chrome进程失败: {e}")
    except ImportError:
        print("⚠️ 未安装psutil库，无法自动终止现有进程")


if __name__ == "__main__":
    kill_existing_processes()
    run_settings()
