import json
from re import S
import wsgiref
import os
import json
import time

# import requests
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By

# from Crypto.Cipher import AES
# import base64
from Crypto.Util.Padding import pad
import tkinter as tk
from settings_window import SettingsWindow
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dingtalk_notify import send_dingtalk_msg

# 全局变量：存储登录状态码
LOGIN_STATUS_CODE = None
from email_sender import send_email


# 读取配置文件
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

import threading

stop_event = threading.Event()  # ← 任何线程都可以 set() 它


# 运行设置窗口的函数
def run_settings_window():
    root = tk.Tk()
    settings_window = SettingsWindow(root, callback=on_config_saved, stop_event=stop_event)
    root.mainloop()


# 在单独线程中启动设置窗口
settings_thread = threading.Thread(target=run_settings_window)
settings_thread.daemon = True


def on_config_saved():
    # 重新读取配置文件
    global config, username, password, load_wait_time
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    username = config["account"]["username"]
    password = config["account"]["password"]
    load_wait_time = config["timing"]["load_wait_time"]

    # === 初始化 Chrome 浏览器 ===
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")


settings_thread.start()

# 等待配置保存后执行后续逻辑
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# 从配置中获取参数
# 不再等待线程完成，直接继续执行主程序
username = config["account"]["username"]
password = config["account"]["password"]
load_wait_time = config["timing"]["load_wait_time"]
loop_interval = config["timing"]["loop_interval"]
dingtalk_times = config["timing"]["dingtalk_times"]
ws_token_key = config["encryption"]["ws_token_key"].encode("utf-8")

# === 初始化 Chrome 浏览器（可视） ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# 启用性能日志以捕获网络请求状态
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
driver = webdriver.Chrome(options=options)

# === 下载 JS 文件的存储目录 ===
JS_SAVE_DIR = "./downloaded_js"
os.makedirs(JS_SAVE_DIR, exist_ok=True)


try:
    # 发送邮件测试
    # send_email("jeking@wic-power.cn", "主题", "内容阿萨德阿斯蒂芬阿斯蒂芬阿斯蒂芬，水岸东方。早开早散会！")
    # send_email("jekingxu@mic-power.cn", "内部测试", "hello", from_addr="service@wic-power.cn")
    # send_email(
    #     "jekingxu@163.com",
    #     "内部测www试",
    #     "hello ,sdlwefawf asdsdfo",
    #     from_addr="531556397@qq.com",
    # )
    # send_email("jekingxu@163.com", "内部测试", "hello", from_addr="service@wic-power.cn")

    # === Step 1: 打开登录页 ===
    driver.get("http://ems.hy-power.net:8114/login")
    settings_window.update_debug_label("登录中...")
    time.sleep(load_wait_time * 2)

    # 设置localStorage中的emsId
    driver.execute_script(
        "localStorage.setItem('local-power-station-active-emsId', 'E6F7D5412A20');"
    )

    # === Step 2: 获取验证码 ===
    canvas = driver.find_element(By.ID, "canvas")
    verification_code = canvas.get_attribute("verificationcode")
    print("\n✅[验证码] =", verification_code)

    # === Step 3: 填写账号密码验证码 ===
    driver.find_element(By.ID, "form_item_username").clear()
    driver.find_element(By.ID, "form_item_username").send_keys(username)

    driver.find_element(By.ID, "form_item_password").clear()
    driver.find_element(By.ID, "form_item_password").send_keys(password)

    driver.find_element(By.CSS_SELECTOR, 'input[placeholder="请输入验证码"]').send_keys(
        verification_code
    )

    # === Step 4: 提交登录表单 ===
    login_button = driver.find_element(By.CSS_SELECTOR, "form.login-form button")
    login_button.click()

    # === Step 5: 等待登录后页面加载完成 ===
    time.sleep(load_wait_time * 2)

    # === Step 6: 打印 cookie、localStorage、sessionStorage ===
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

    print("\n✅ [当前页面 URL]:", driver.current_url)

    # === Step 7: 提取所有 JS 脚本 URL ===
    script_elements = driver.find_elements(By.TAG_NAME, "script")
    time.sleep(2)

    js_urls = []
    for script in script_elements:
        src = script.get_attribute("src")
        if src:
            full_url = urljoin(driver.current_url, src)
            js_urls.append(full_url)

    # print(f"\n🧠 共发现 {len(js_urls)} 个 JS 文件，开始下载...\n")

    # === Step 8: 下载 JS 文件 ===
    for idx, js_url in enumerate(js_urls, 1):
        try:
            print(f"\n🔽 [{idx}/{len(js_urls)}] 下载: {js_url}")
            # resp = requests.get(js_url, timeout=10)
            # filename = os.path.basename(urlparse(js_url).path)
            # if not filename.endswith(".js"):
            #     filename = f"script_{idx}.js"
            # file_path = os.path.join(JS_SAVE_DIR, filename)
            # with open(file_path, "w", encoding="utf-8") as f:
            #     f.write(resp.text)
        except Exception as e:
            print(f"\n❌ 下载失败: {js_url} 错误: {e}")

    # print(f"\n✅ 所有 JS 文件已保存到：{os.path.abspath(JS_SAVE_DIR)}")
    print("\n🟢 登录已完成...")
    # ===循环检测网页内容===================
    getDataCounts = 0
    # 循环执行标志
    continue_running = True

    # while continue_running:
    while not stop_event.is_set():

        try:

            # 再获取最新地址
            print(f"\n✅ 当前页面实际地址：{driver.current_url}")

            # ===================检测完整内容是否是默认数据方法1==================
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
            # 保持热连接 防止页面跳转
            driver.execute_script("window.scrollBy(0, 10);")  # 滚动
            driver.execute_script(
                "window.dispatchEvent(new Event('mousemove'))"
            )  # 模拟鼠标事件
            # 等待页面加载
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete",
                message="网页未在20秒内加载完成",
            )
            # // 分阶段等待：1. ECharts库加载 2. 图表实例创建
            WebDriverWait(driver, 100).until(
                lambda d: d.execute_script(
                    "return typeof window.echarts !== 'undefined' && typeof window.echarts.getInstanceByDom === 'function'"
                ),
                message="ECharts库未在100秒内加载完成",
            )
            # // 等待图表实例创建（增加短暂延迟确保数据绑定）
            WebDriverWait(driver, 100).until(
                lambda d: d.execute_script(
                    """
                      // 查找已初始化的ECharts实例
                      const allElements = document.getElementsByTagName('*');
                      for (let i = 0; i < allElements.length; i++) {
                          const instance = window.echarts.getInstanceByDom(allElements[i]);
                          if (instance) return true;
                      }
                      return false;
                      """
                ),
                message="ECharts图表实例未在100秒内创建",
            )
            # // 额外等待数据加载
            time.sleep(load_wait_time + 20)
            # 执行检测脚本
            result = driver.execute_script(detect_script)
            print(f"\n📊 数据检测结果: {result}")

            if "87" in result:
                print("\n⚠️ 警告: 可能未加载真实数据")
                content = (
                    f"Event Type: BY-EMS-01-系统可用性探测通知\n"
                    f"System Message: Alarm\警告!\n"
                    f"checkUrl: {driver.current_url}\n"
                    f"message: ⚠️ 警告: 网站全是默认值，可能未收到真实数据，请检查！\n"
                    f"数据检测结果: {result}\n"
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
                print(f"✅getDataCounts = {getDataCounts}")
            else:
                print("\n✅ 数据加载正常")
                ErrorContent = (
                    f"Event Type: BY-EMS-01-系统可用性探测通知\n"
                    f"System Message: Normal\正常!\n"
                    f"checkUrl: {driver.current_url}\n"
                    f"message: ⚠️ 警告: 网站全是默认值，可能未收到真实数据，请检查！\n"
                    f"数据检测结果: {result}\n"
                    f"webSiteState: Accessible\访问正常！"
                )
                if getDataCounts >= dingtalk_times * 20:
                    send_dingtalk_msg(ErrorContent)
                    getDataCounts = 0
                else:
                    print(
                        f"\n❌还要间隔 {dingtalk_times-getDataCounts} 次后再次发送钉钉消息！"
                    )

            driver.refresh()  # 刷新页面
            print("\n✅ 刷新页面成功")

            print(f"\n等待 {loop_interval} 秒后执行下一次循环...")

            time.sleep(loop_interval)

        except Exception as e:
            # 统一循环出错
            print(f"\n循环出错...{e}")


except Exception as e:
    print("\n⚠️用户中断程序，退出循环...")
    continue_running = False

    # 程序结束时关闭浏览器
    driver.quit()
    print("\n✅ 程序结束，关闭了浏览器")
finally:
    # === Step 9: 保持浏览器窗口打开 ===
    # input("\n🟢 检测已完成，按回车键关闭浏览器...")  #按回车即可关闭浏览器窗口

    # 程序结束时关闭浏览器
    driver.quit()
    print("\n⚠️程序正常跑完结束...")
    print("⚠️请确保浏览器已关闭...")
    print("🟢 浏览器已关闭，程序退出")
    os._exit(0)  # 彻底结束进程，防止残余后台线程
