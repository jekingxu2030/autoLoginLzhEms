import json
import os
import time
import threading
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
from settings_window import SettingsWindow
from dingtalk_notify import send_dingtalk_msg
from email_sender import send_email

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
        time.sleep(load_wait_time * 2)

        driver.execute_script(
            "localStorage.setItem('local-power-station-active-emsId', 'E6F7D5412A20');"
        )

        # === 登录流程 ===
        canvas = driver.find_element(By.ID, "canvas")
        verification_code = canvas.get_attribute("verificationcode")
        print("\n✅[验证码] =", verification_code)

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

        print("✅ 登录成功，开始循环检测...")

        getDataCounts = 0

        while not stop_event.is_set():
            try:
                print(f"\n当前页面: {driver.current_url}")

                driver.execute_script("window.scrollBy(0, 10);")
                driver.execute_script("window.dispatchEvent(new Event('mousemove'))")

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
                  return (function() {
                      if (!window.echarts || !window.echarts.getInstanceByDom) {
                          return 'ECharts 未定义或未加载';
                      }
                      const charts = [];
                      document.querySelectorAll('div').forEach(el => {
                          try {
                              const chart = window.echarts.getInstanceByDom(el);
                              if (chart) charts.push(chart);
                          } catch (e) {
                          return e;
                          }
                      });
                      if (charts.length === 0) return '未找到图表实例';
                      let allDefault = true;
                      charts.forEach(chart => {
                          const option = chart.getOption();
                          if (option && option.series) {
                              option.series.forEach(series => {
                                  if (series.data) {
                                      const data = Array.isArray(series.data) ? series.data : [series.data];
                                      data.forEach(item => {
                                          const value = typeof item === 'object' ? item.value : item;
                                          if (value !== 87) allDefault = false;
                                      });
                                  }
                              });
                          }
                      });
                      return allDefault ? '所有数据均为默认值87' : '检测到真实数据';
                  })();
                  """
                result = driver.execute_script(detect_script)
                print("检测结果:", result)

                if "87" in result:
                    content = (
                        f"evente: BY-EMS-01-系统可用性探测通知\n"
                        f"state: Alarm\警告!\n"
                        f"checkUrl: {driver.current_url}\n"
                        f"message: ⚠️ 警告: 网站全是默认值，可能未收到真实数据，请检查！\n"
                        f"result: {result}\n"
                        f"webSiteState: Accessible\访问正常"
                    )
                    if getDataCounts >= dingtalk_times:
                        send_dingtalk_msg(content)
                        getDataCounts = 0
                    else:
                        print(
                            f"\n❌还要间隔 {dingtalk_times-getDataCounts} 次后再次发送钉钉消息！"
                        )
                        getDataCounts += 1
                        print(f"✅已间隔次数 = {getDataCounts}")
                else:
                    print("\n✅ 数据加载正常")
                    ErrorContent = (
                    f"event: BY-EMS-01-系统可用性探测通知\n"
                    f"state: Normal\正常!\n"
                    f"checkUrl: {driver.current_url}\n"
                    f"message: ⚠️ 警告: 网站全是默认值，可能未收到真实数据，请检查！\n"
                    f"result: {result}\n"
                    f"webSiteState: Accessible\访问正常！"
                    )
                    if getDataCounts >= dingtalk_times * 20:
                        send_dingtalk_msg(ErrorContent)
                        getDataCounts = 0
                    else:
                        print(
                         f"\n❌还要间隔 {dingtalk_times-getDataCounts} 次后再次发送钉钉消息！"
                       )

                driver.refresh()
                print("\n✅ 刷新页面")
                print(f"\n等待 {loop_interval+(load_wait_time*4)+26} 秒后执行下一次循环...")
                time.sleep(loop_interval)

            except Exception as e:
                print("循环错误:", e)

    except Exception as e:
        print("主逻辑异常:", e)
    finally:
        if driver:
            driver.quit()
        print("✅ 线程退出")


# === 设置窗口线程 ===
def run_settings():
    global settings_window
    root = tk.Tk()
    settings_window = SettingsWindow(
        root, callback=start_main_logic, stop_event=stop_event
    )
    root.mainloop()


# === 回调触发主逻辑 ===
def start_main_logic():
    if not running_event.is_set():
        logic_thread = threading.Thread(target=main_logic, daemon=True)
        logic_thread.start()
        running_event.set()
        print("🚀 主线程已启动")


if __name__ == "__main__":
    run_settings()
