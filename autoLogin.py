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
from ems_ws_monitor import EmsWsMonitor
from datetime import datetime

# 将WebSocket URL写入config.ini文件
import configparser

# from ems_ws_monitor import EmsWsInterceptor

config = configparser.ConfigParser()

# === 路径 ===
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
JS_SAVE_DIR = "./downloaded_js"
os.makedirs(JS_SAVE_DIR, exist_ok=True)

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
    settings_window.log_lbl.after(0, lambda: settings_window.update_debug_label(text))


def set_config_value(filename, section, key, value):
    """
    写入或更新配置文件中的指定值
    :param filename: 配置文件名（如 config.ini）
    :param section: 区段名（如 websocket）
    :param key: 键名（如 url）
    :param value: 键值（如 ws://xxx）
    """
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
            print("✅ 捕获到WebSocket URL:", ws_url)

            # 读取ini并写入配置文件
            set_config_value("config.ini", "websocket", "url", ws_url)
            thread_safe_update_debug_label(
                        f"✅ 获取到的 WebSocket 完整地址：{ws_url[30]}"
                    )

            return ws_url

    return None


# === 主执行函数（登录 + 探测） ===
def main_logic():
    try:

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        username = config["account"]["username"]
        password = config["account"]["password"]
        load_wait_time = config["timing"]["load_wait_time"]
        loop_interval = config["timing"]["loop_interval"]
        dingtalk_times = config["timing"]["dingtalk_times"]
        # ws_token_key = config["encryption"]["ws_token_key"].encode("utf-8")

        # === 浏览器设置 ===
        global driver
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        driver = webdriver.Chrome(options=options)

        driver.get("http://ems.hy-power.net:8114/login")
        # settings_window.update_debug_label("登录中...")
        thread_safe_update_debug_label("请求网页中...")
        print(f"\n✅[请求 {driver.current_url} 已完成")
        time.sleep((load_wait_time + 10))

        driver.execute_script(
            "localStorage.setItem('local-power-station-active-emsId', 'E6F7D5412A20');"
        )

        # === 登录流程 ===
        canvas = driver.find_element(By.ID, "canvas")
        verification_code = canvas.get_attribute("verificationcode")
        print("\n✅[验证码] =", verification_code)
        thread_safe_update_debug_label(f"✅[验证码] ={verification_code}")

        # 填表并登录
        driver.find_element(By.ID, "form_item_username").send_keys(username)
        driver.find_element(By.ID, "form_item_password").send_keys(password)
        driver.find_element(
            By.CSS_SELECTOR, 'input[placeholder="请输入验证码"]'
        ).send_keys(verification_code)
        time.sleep(2)
        # 点击登录
        driver.find_element(By.CSS_SELECTOR, "form.login-form button").click()

        time.sleep(load_wait_time + 5)

        # 读取cookie
        print("\n✅ [Cookies]:")
        for cookie in driver.get_cookies():
            if cookie:
                print(f"\ncookie：{cookie['name']} = {cookie['value']}")
                key = str(cookie["name"])     # 取 name 并转字符串
                value = str(cookie["value"])  # 取 value 并转字符串
                set_config_value(
                    # "config.ini", "cookie", f"{cookie['name']}", f"{cookie['value']}"
                     "config.ini", "cookie",key,value )

        # 读取localStorage
        print("\n✅ [localStorage]:")
        time.sleep(2)
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
        print(json.dumps(local_storage, indent=2, ensure_ascii=False))
        for key, value in local_storage.items():
            key = str(key)
            value = str(value)
            set_config_value("config.ini", "localStorage", key, value)
            print(f"\nlocalStorage:{key} = {value}")

        # 读取sessionStorage
        print("\n✅ [sessionStorage]:")
        time.sleep(2)
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
            key = str(key)
            value = str(value)
            set_config_value("config.ini", "session_storage", key, value)
            print(f"\nsession_storage:{key} = {value}")
        print("\n" + json.dumps(session_storage, indent=2, ensure_ascii=False))

        thread_safe_update_debug_label("缓存参数获取或设置完毕，开始探测内容...")
        print("✅ 登录成功，开始循环检测...")
        sendDDtotal = 0
        intervalCounts = 0  # 正常状态下推送间隔时间

        # 循环检测
        while not stop_event.is_set():
            try:
                print(f"\n当前页面: {driver.current_url}")
                thread_safe_update_debug_label(f"\n当前页面: {driver.current_url}")
                # 判断页面是否加载完成
                WebDriverWait(driver, 20).until(
                    lambda d: d.execute_script("return document.readyState")
                    == "complete"
                )
                # 检测echarts是否加载完成
                WebDriverWait(driver, 100).until(
                    lambda d: d.execute_script(
                        "return typeof window.echarts !== 'undefined'"
                    )
                )
                # 检测echarts是否加载完成
                WebDriverWait(driver, 100).until(
                    lambda d: d.execute_script(
                        """
                    const allElements = document.getElementsByTagName('*');
                    for (let i = 0; i < allElements.length; i++) {
                        const instance = window.echarts.getInstanceByDom(allElements[i]);
                        if (instance) return true;
                    }
                    return false;"""
                    )
                )
                # 模拟操作鼠标
                driver.execute_script("window.scrollBy(0, 10);")
                driver.execute_script("window.dispatchEvent(new Event('mousemove'))")
                thread_safe_update_debug_label("模拟网页操作，防止掉线...")
                time.sleep(loop_interval + 20)

           
                #  ==================================================== #            
                # 检测WS URL
                ws_url = get_ws_url(driver)  # --更新ws连接字套
                # 每次调用获取一次 rtv 推送（若存在）
                ws_monitor = EmsWsMonitor(driver, timeout=20)
                status = ws_monitor.start()
                print("检测状态：", status)
                if status:
                    # 你可以自行判断数据有效性
                    print("✅ 成功拦截到RTV推送")
                    lsstSendtTime = (
                        (loop_interval * 3) + (load_wait_time * 2) + 51
                    ) * (dingtalk_times - intervalCounts)
              
                    if status == "ok":
                        print("✅ 网站数据正常")
                        thread_safe_update_debug_label(f"✅ 网站实时数据正常")
                        print(f"\n✅ 数据加载正常,{intervalCounts}")
                        if intervalCounts >= dingtalk_times * 24:  # 正常要比故障长20倍
                            Content = (
                                f"Event: BY-01-EMS_StatusCheck\n"
                                f"State: Normal!\n"
                                f"CheckUrl: {driver.current_url}\n"
                                f"Message:网站数据正常，收到真实数据，请检查！\n"
                                f"WebSiteState: Accessible！"
                            )

                            thread_safe_update_debug_label(
                                f"正常状态推送间隔时长:"
                                + str(lsstSendtTime * 24)
                                + "秒"
                            )
                            print(
                                f"正常状态推送间隔时长:"
                                + str(lsstSendtTime * 24)
                                + "秒"
                            )
                            # print(f"发送的数据2：{Content}")
                            send_dingtalk_msg(Content)
                            sendDDtotal += 1
                            intervalCounts = 0
                            send_email(
                                [
                                    # "jekingxu@mic-power.cn",
                                    # "jekingxu@163.com",
                                    # "marcin.lee@wic-power.com",
                                    "wicpower2023@gmail.com",
                                    "531556397@qq.com",
                                    "ng.support@baiyiled.nl",
                                ],
                                "【EMS Events】",
                                f"《提示!》\n\n尊敬的用户您好！您的215P01项目EMS后台系统数据“正常” ，请您放心运行!谢谢!\nCheckUrl: {driver.current_url}\n\n\n检测时间：{datetime.now()}",
                                # from_addr="service@wic-power.com",
                                from_addr="jekingxu@163.com",
                            )
                            thread_safe_update_debug_label("正常状态推送定消息完成...")
                        else:
                            print(
                                f"\n ⚠️还要间隔 {dingtalk_times-intervalCounts} 次后再次发送钉钉消息！"
                            )
                            thread_safe_update_debug_label(
                                f"⚠️还要间隔 {dingtalk_times-intervalCounts} 次后再次发送钉钉消息！"
                            )
                            intervalCounts += 1
                    elif status == "empty":
                        print("⚠️ 网站可访问但数据为空/默认值")
                        thread_safe_update_debug_label(f"❌ 网站实时数据异常")
                        errocontent = (
                            f"Event: BY-01-EMS_StatusCheck\n"
                            f"State: Alarm!\n"
                            f"CheckUrl: {driver.current_url}\n"
                            f"Message:网站全是默认值或空值，可能未收到真实数据，请检查！\n"
                            f"WebSiteState: Accessible"
                        )
                        if intervalCounts >= dingtalk_times:  # 正常的比故障长20倍
                            # print(f"发送的数据：{errocontent}")
                            send_dingtalk_msg(errocontent)
                            sendDDtotal += 1
                            intervalCounts = 0
                            thread_safe_update_debug_label("推送故障钉钉消息完成...")
                            send_email(
                                [
                                    # "jekingxu@mic-power.cn",
                                    # "jekingxu@163.com",
                                    # "marcin.lee@wic-power.com",
                                    "wicpower2023@gmail.com",
                                    "531556397@qq.com",
                                    # "ng.support@baiyiled.nl",
                                ],
                                "【EMS Events】",
                                f"《警告!》\n\n尊敬的用户您好！我们检测到您的215P01项目EMS后台系统数据“empty”异常！请您尽快检查和处理!谢谢!\nCheckUrl: {driver.current_url}\n\n\n事件时间：{datetime.now()}",
                                # from_addr="531556397@qq.com",
                                from_addr="jekingxu@163.com",
                            )
                        else:
                            print(
                                f"\n ⚠️还要间隔 {dingtalk_times-intervalCounts} 次后再次发送钉钉消息！"
                            )
                            thread_safe_update_debug_label(
                                f"⚠️还要间隔 {dingtalk_times-intervalCounts} 次后再次发送钉钉消息！"
                            )
                            intervalCounts += 1
                    elif status == "no_msg":
                        print("❌ 超时未收到任何推送,网站异常")
                        thread_safe_update_debug_label(f"❌ 网站实时数据异常")
                        errocontent = (
                            f"Event: BY-01-EMS_StatusCheck\n"
                            f"State: Alarm!\n"
                            f"CheckUrl: {driver.current_url}\n"
                            f"Message:网站请求数据超时，请检查！\n"
                            f"WebSiteState: Accessible"
                        )
                        if intervalCounts >= dingtalk_times:  # 正常的比故障长20倍
                            # print(f"发送的数据：{errocontent}")
                            send_dingtalk_msg(errocontent)
                            sendDDtotal += 1
                            intervalCounts = 0
                            send_email(
                                [
                                    # "jekingxu@mic-power.cn",
                                    # "jekingxu@163.com",
                                    # "marcin.lee@wic-power.com",
                                    "531556397@qq.com",
                                    "wicpower2023@gmail.com",
                                    # "ng.support@baiyiled.nl",
                                ],
                                "【EMS Events】",
                                f"《警告!》\n\n尊敬的用户您好！我们检测到您的215P01项目EMS后台系统数据“no_data”异常！请您尽快检查和处理!谢谢!\nCheckUrl: {driver.current_url}\n\n\n事件时间：{datetime.now()}",
                                # from_addr="service@wic-power.com",
                                #  from_addr="531556397@qq.com",  #QQ发送时必须用原发送邮箱名称
                                from_addr="jekingxu@163.com",
                            )
                            thread_safe_update_debug_label("推送故障钉钉消息完成...")
                        else:
                            print(
                                f"\n ⚠️还要间隔 {dingtalk_times-intervalCounts} 次后再次发送钉钉消息！"
                            )
                            thread_safe_update_debug_label(
                                f"⚠️还要间隔 {dingtalk_times-intervalCounts} 次后再次发送钉钉消息！"
                            )
                            intervalCounts += 1
                    elif status == "no_ws":
                        print("❌ WebSocket 连接失败")
                        thread_safe_update_debug_label(f"❌ 网站连接异常")
                        errocontent = (
                            f"Event: BY-01-EMS_StatusCheck\n"
                            f"State: Alarm!\n"
                            f"CheckUrl: {driver.current_url}\n"
                            f"Message:网站WS数据连接失败，请检查！\n"
                            f"WebSiteState: Accessible"
                        )
                        if intervalCounts >= dingtalk_times:  # 正常的比故障长20倍
                            # print(f"发送的数据：{errocontent}")
                            send_dingtalk_msg(errocontent)
                            intervalCounts = 0
                            sendDDtotal += 1
                            send_email(
                                [
                                    # "jekingxu@mic-power.cn",
                                    # "jekingxu@163.com",
                                    # "marcin.lee@wic-power.com",
                                    "wicpower2023@gmail.com",
                                    "531556397@qq.com",
                                    # "ng.support@baiyiled.nl",
                                ],
                                "【EMS Events】",
                                f"《警告!》\n\n尊敬的用户您好！我们检测到您的215P01项目EMS后台系统数据“no_ws”异常！请您尽快检查和处理!谢谢!\nCheckUrl: {driver.current_url}\n\n\n事件时间：{datetime.now()}",
                                # from_addr="531556397@qq.com",
                                from_addr="jekingxu@163.com",
                            )
                            thread_safe_update_debug_label("推送故障钉钉消息完成...")
                        else:
                            print(
                                f"\n ⚠️还要间隔 {dingtalk_times-intervalCounts} 次后再次发送钉钉消息！"
                            )
                            thread_safe_update_debug_label(
                                f"⚠️还要间隔 {dingtalk_times-intervalCounts} 次后再次发送钉钉消息！"
                            )
                            intervalCounts += 1
                    elif status == "error":
                        print("❌ WebSocket 连接错误")
                        thread_safe_update_debug_label(f"❌ 网站连接错误")
                        errocontent = (
                          f"Event: BY-01-EMS_StatusCheck\n"
                          f"State: Alarm!\n"
                          f"CheckUrl: {driver.current_url}\n"
                          f"Message:网站WS数据连接错误，请检查！\n"
                          f"WebSiteState: cantConnect"
                      )
                        if intervalCounts >= dingtalk_times:  # 正常的比故障长20倍
                            send_dingtalk_msg(errocontent)
                            intervalCounts = 0
                            sendDDtotal += 1
                            send_email(
                              [
                                  # "jekingxu@mic-power.cn",
                                  # "jekingxu@163.com",
                                  # "marcin.lee@wic-power.com",
                                  "wicpower2023@gmail.com",
                                  "531556397@qq.com",
                                  # "ng.support@baiyiled.nl",
                              ],
                              "【EMS Events】",
                              f"《警告!》\n\n尊敬的用户您好！我们检测到您的215P01项目EMS连接异常！请您尽快检查和处理!谢谢!\nCheckUrl: {driver.current_url}\n\n\n事件时间：{datetime.now()}",
                              # from_addr="531556397@qq.com",
                              from_addr="jekingxu@163.com",
                          )
                            thread_safe_update_debug_label("推送故障钉钉消息完成...")
                        else:
                            print(
                              f"\n ⚠️还要间隔 {dingtalk_times-intervalCounts} 次后再次发送钉钉消息！"
                          )
                            thread_safe_update_debug_label(
                              f"⚠️还要间隔 {dingtalk_times-intervalCounts} 次后再次发送钉钉消息！"
                          )
                            intervalCounts += 1

                    print(f"✅已间隔次数 = {intervalCounts}")
                else:
                    print("❌ 未捕获到WebSocket URL")

                # ========================================
                time.sleep(loop_interval)
                driver.refresh()
                print("\n✅ 刷新页面")
                print(
                    f"\n等待至少 {(loop_interval*3)+(load_wait_time*3)+51+(dingtalk_times-intervalCounts)} 秒后执行下一次循环..."
                )
                thread_safe_update_debug_label(
                    f"等待至少 {(loop_interval*3)+(load_wait_time*3)+51+(dingtalk_times-intervalCounts)} 秒后执行下一次循环..."
                )

                print(f"本轮已发送钉钉：{ sendDDtotal}次")
                thread_safe_update_debug_label(f"本次已发送钉钉：{ sendDDtotal}次")
            except Exception as e:
                print("循环错误:", e)
                thread_safe_update_debug_label(f"❌循环错误" + str(e))

    except Exception as e:
        print("主线程逻辑异常:", e)
        thread_safe_update_debug_label(f"❌主逻辑异常" + str(e))
    finally:
        if driver:
            try:
                thread_safe_update_debug_label(f"❌线程退出,正在关闭浏览器...")
                print("⚠️线程退出,正在关闭浏览器")
                driver.quit()
                time.sleep(12)  # 确保浏览器完全关闭
                if hasattr(driver, "service") and driver.service.process:
                    driver.service.process.terminate()
            except Exception as e:
                print(f"关闭浏览器时出错: {e}")
                thread_safe_update_debug_label(f"❌关闭浏览器时出错: {e}")


# === 设置窗口线程 ===
def run_settings():
    global settings_window
    root = tk.Tk()

    def on_closing():
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


if __name__ == "__main__":
    run_settings()
