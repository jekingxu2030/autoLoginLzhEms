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
from email_sender import send_email
from selenium import webdriver
import time
import json
from selenium import webdriver

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


def thread_safe_update_debug_label(text):
    settings_window.log_lbl.after(0, lambda: settings_window.update_debug_label(text))


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
        time.sleep(load_wait_time * 2)

        driver.execute_script(
            "localStorage.setItem('local-power-station-active-emsId', 'E6F7D5412A20');"
        )

        # === 登录流程 ===
        canvas = driver.find_element(By.ID, "canvas")
        verification_code = canvas.get_attribute("verificationcode")
        print("\n✅[验证码] =", verification_code)
        thread_safe_update_debug_label(f"✅[验证码] ={verification_code}")

        driver.find_element(By.ID, "form_item_username").send_keys(username)
        driver.find_element(By.ID, "form_item_password").send_keys(password)
        driver.find_element(
            By.CSS_SELECTOR, 'input[placeholder="请输入验证码"]'
        ).send_keys(verification_code)
        time.sleep(2)
        driver.find_element(By.CSS_SELECTOR, "form.login-form button").click()

        time.sleep(load_wait_time * 1)

        print("\n✅ [Cookies]:")
        for cookie in driver.get_cookies():
            print(f"\n{cookie['name']} = {cookie['value']}")

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
        print("\n" + json.dumps(session_storage, indent=2, ensure_ascii=False))
        thread_safe_update_debug_label("缓存参数获取或设置完毕，开始探测内容...")
        print("✅ 登录成功，开始循环检测...")


        def get_ws_url():
            logs = driver.get_log('performance')
            for entry in logs:
                message = json.loads(entry['message'])['message']
                if message['method'] == 'Network.webSocketCreated':
                    ws_url = message['params']['url']
                    print("捕获到WebSocket URL:", ws_url)
                    return ws_url

        ws_url = get_ws_url()
        print("✅ 获取到的 WebSocket 完整地址：", ws_url)

        getDataCounts = 0   #正常状态下推送间隔时间

        while not stop_event.is_set():
            try:
                print(f"\n当前页面: {driver.current_url}")
                thread_safe_update_debug_label(f"\n当前页面: {driver.current_url}")

                driver.execute_script("window.scrollBy(0, 10);")
                driver.execute_script("window.dispatchEvent(new Event('mousemove'))")
                thread_safe_update_debug_label("模拟网页操作，防止掉线...")

                WebDriverWait(driver, 20).until(
                    lambda d: d.execute_script("return document.readyState")
                    == "complete"
                )
                WebDriverWait(driver, 100).until(
                    lambda d: d.execute_script(
                        "return typeof window.echarts !== 'undefined'"
                    )
                )
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

                time.sleep(load_wait_time + 20)
                detect_script = """
                                 return (function () {
                            const result = [];
                            document.querySelectorAll('div').forEach((el, idx) => {
                                try {
                                    const inst = window.echarts.getInstanceByDom(el);
                                    if (!inst) return;
                                    const opt = inst.getOption();
                                    if (!opt.series) return;
                                    opt.series.forEach((s, sIdx) => {
                                        // 取前 10 个点做样本
                                        const sample = (Array.isArray(s.data) ? s.data : [s.data])
                                                        .slice(0, 20)
                                                        .map(d => (typeof d === 'object' ? d.value : d));
                                        result.push({ chart: idx, series: sIdx, sample });
                                    });
                                } catch (e) { /* 忽略 */ }
                            });
                            return JSON.stringify(result);
                        })();
                             
                  """
                result = driver.execute_script(detect_script)
                time.sleep(2)

                print("检测结果:", result)
                thread_safe_update_debug_label(f"检测结果：{result[:20]}")

                if "87" in result:
                    print("\n❌数据加载异常")
                    errocontent = (
                        f"Event: BY-01-EMS_StatusCheck\n"
                        f"State: Alarm!\n"
                        f"CheckUrl: {driver.current_url}\n"
                        f"Message:网站全是默认值，可能未收到真实数据，请检查！\n"
                        f"Result: {result[20]}\n"
                        f"WebSiteState: Accessible"
                    )
                    if getDataCounts >= dingtalk_times:
                        print(f"发送的数据：{errocontent}")
                        send_dingtalk_msg(errocontent)
                        getDataCounts = 0
                        thread_safe_update_debug_label("推送故障钉钉消息完成...")
                    else:
                        print(
                            f"\n ⚠️还要间隔 {dingtalk_times-getDataCounts} 次后再次发送钉钉消息！"
                        )
                        thread_safe_update_debug_label(
                            f"⚠️还要间隔 {dingtalk_times-getDataCounts} 次后再次发送钉钉消息！"
                        )
                        getDataCounts += 1
                        print(f"✅已间隔次数 = {getDataCounts}")
                else:
                    print(f"\n✅ 数据加载正常,{getDataCounts}")

                    if getDataCounts >= 1:  # 正常要比故障长20倍
                        Content = (
                            f"Event: BY-01-EMS_StatusCheck\n"
                            f"State: Normal!\n"
                            f"CheckUrl: {driver.current_url}\n"
                            f"Message:网站数据正常，收到真实数据，请检查！\n"
                            f"Result: {result[:20]}\n"
                            f"WebSiteState: Accessible！"
                        )
                     
                        faultTime = (loop_interval + (load_wait_time * 4) + 26) * 10
                        thread_safe_update_debug_label(
                            f"正常状态推送间隔时长:" + str(faultTime) + "秒"
                        )
                        print(f"正常状态推送间隔时长:" + str(faultTime) + "秒")
                        print(f"发送的数据2：{Content}")
                        send_dingtalk_msg(Content)
                        getDataCounts = 0
                        thread_safe_update_debug_label("正常状态推送定消息完成...")
                    else:
                        print(
                            f"\n ⚠️还要间隔 {dingtalk_times-getDataCounts} 次后再次发送钉钉消息！"
                        )
                        thread_safe_update_debug_label(
                            f"⚠️还要间隔 {dingtalk_times-getDataCounts} 次后再次发送钉钉消息！"
                        )
                        getDataCounts += 1
                driver.refresh()
                print("\n✅ 刷新页面")
                print(
                    f"\n等待 {loop_interval+(load_wait_time*4)+26} 秒后执行下一次循环..."
                )
                thread_safe_update_debug_label(
                    f"等待 {loop_interval+(load_wait_time*4)+26} 秒后执行下一次循环..."
                )
                time.sleep(loop_interval)

            except Exception as e:
                print("循环错误:", e)
                thread_safe_update_debug_label(f"❌循环错误" + str(e))

    except Exception as e:
        print("主逻辑异常:", e)
        thread_safe_update_debug_label(f"❌主逻辑异常" + str(e))
    finally:
        if driver:
            thread_safe_update_debug_label(f"❌线程退出,关闭浏览器...")
            print("⚠️线程退出")
            driver.quit()


# === 设置窗口线程 ===
# 定义一个run_settings函数，用于运行设置窗口
def run_settings():
    # 声明一个全局变量settings_window
    global settings_window
    # 创建一个Tkinter窗口
    root = tk.Tk()
    # 创建一个SettingsWindow对象，并传入root、callback和stop_event参数
    settings_window = SettingsWindow(
        root, callback=start_main_logic, stop_event=stop_event
    )
    # 进入Tkinter的主循环
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
