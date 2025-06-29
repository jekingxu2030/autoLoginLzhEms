"""
一、这个模块是用于自动登录网站的
  1.登录网站地址：http://ems.hy-power.net:8114/login
一、这个模块是用于自动登录网站的
1.登录网站地址：http://ems.hy-power.net:8114/login
2.登录元素定位：
登录账户：WC001，表单位置：<input type="text" class="ant-input css-111zvph" autocomplete="on" placeholder="请输入登录账号" id="form_item_username" value="WC001">
密码：123456789，表单位置：<input type="password" class="ant-input css-111zvph" autocomplete="on" placeholder="请输入密码" id="form_item_password" value="123456789">
验证码表单位置：<input type="text" class="ant-input css-111zvph" placeholder="请输入验证码" value="">
登录表单元素如下：
<form data-v-e28a0735="" data-v-f94de0b4="" class="ant-form ant-form-horizontal css-111zvph login-form">
3.验证码获取方法：在登录页面的验证码元素中内置了验证码属性值
4.验证码所在元素如下：
<canvas data-v-83eafb9b="" data-v-e28a0735="" id="canvas" class="verify-canvas" width="120" height="40" verificationcode="n6XQ"></canvas>
5.其中的verificationcode属性值就是验证码的值
6.填充账户、密码、验证码后提交登录表单
7.登录后将服务器设置在本地的cookie和section，以及其他服务器传来的参数全部读出输出
备注：AI分析用什么语言合适就用什么语言开发代码，登录时间需要延长点，登录窗口可以保持开启；
二、等待设计  
"""
import json
import wsgiref
import os
import time
import requests
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from Crypto.Cipher import AES
import base64
from Crypto.Util.Padding import pad
import tkinter as tk
from settings_window import SettingsWindow

# 读取配置文件
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# 显示设置窗口
root = tk.Tk()
app = SettingsWindow(root)
root.mainloop()

# 重新读取配置文件
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 从配置中获取参数
username = config['account']['username']
password = config['account']['password']
load_wait_time = config['timing']['load_wait_time']
loop_interval = config['timing']['loop_interval']
ws_token_key = config['encryption']['ws_token_key'].encode('utf-8')

# === 初始化 Chrome 浏览器（可视） ===
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)

# === 下载 JS 文件的存储目录 ===
JS_SAVE_DIR = "./downloaded_js"
os.makedirs(JS_SAVE_DIR, exist_ok=True)

# 循环执行标志
continue_running = True

while continue_running:

  try:
    # === Step 1: 打开登录页 ===
    driver.get("http://ems.hy-power.net:8114/login")
    time.sleep(load_wait_time)

    # === Step 2: 获取验证码 ===
    canvas = driver.find_element(By.ID, "canvas")
    verification_code = canvas.get_attribute("verificationcode")
    print("[验证码] =", verification_code)

    # === Step 3: 填写账号密码验证码 ===
    driver.find_element(By.ID, "form_item_username").clear()
    driver.find_element(By.ID, "form_item_username").send_keys(username)

    driver.find_element(By.ID, "form_item_password").clear()
    driver.find_element(By.ID, "form_item_password").send_keys(password)

    driver.find_element(By.CSS_SELECTOR, 'input[placeholder="请输入验证码"]').send_keys(verification_code)

    # === Step 4: 提交登录表单 ===
    login_button = driver.find_element(By.CSS_SELECTOR, "form.login-form button")
    login_button.click()

    # === Step 5: 等待登录后页面加载完成 ===
    time.sleep(load_wait_time)

    # === Step 6: 打印 cookie、localStorage、sessionStorage ===
    print("\n✅ [Cookies]:")

    for cookie in driver.get_cookies():
        print(f"{cookie['name']} = {cookie['value']}")

    print("\n✅ [localStorage]:")
    local_storage = driver.execute_script("""
        let items = {};
        for (let i = 0; i < localStorage.length; i++) {
            let k = localStorage.key(i);
            items[k] = localStorage.getItem(k);
        }
        return items;
    """)
    print(json.dumps(local_storage, indent=2, ensure_ascii=False))

    print("\n✅ [sessionStorage]:")
    session_storage = driver.execute_script("""
        let items = {};
        for (let i = 0; i < sessionStorage.length; i++) {
            let k = sessionStorage.key(i);
            items[k] = sessionStorage.getItem(k);
        }
        return items;
    """)
    print(json.dumps(session_storage, indent=2, ensure_ascii=False))

    print("\n✅ [当前页面 URL]:", driver.current_url)

    # === Step 7: 提取所有 JS 脚本 URL ===
    script_elements = driver.find_elements(By.TAG_NAME, "script")
    js_urls = []
    for script in script_elements:
        src = script.get_attribute("src")
        if src:
            full_url = urljoin(driver.current_url, src)
            js_urls.append(full_url)

    print(f"\n🧠 共发现 {len(js_urls)} 个 JS 文件，开始下载...\n")

    # === Step 8: 下载 JS 文件 ===
    for idx, js_url in enumerate(js_urls, 1):
        try:
            print(f"🔽 [{idx}/{len(js_urls)}] 下载: {js_url}")
            resp = requests.get(js_url, timeout=10)
            filename = os.path.basename(urlparse(js_url).path)
            if not filename.endswith(".js"):
                filename = f"script_{idx}.js"
            file_path = os.path.join(JS_SAVE_DIR, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(resp.text)
        except Exception as e:
            print(f"❌ 下载失败: {js_url} 错误: {e}")

    print(f"\n✅ 所有 JS 文件已保存到：{os.path.abspath(JS_SAVE_DIR)}")

    # === Step 9: 保持浏览器窗口打开 ===
    input("\n🟢 登录已完成，JS 已下载，按回车键关闭浏览器...")

    # =====================计算ws-token==================
    # 确保密钥长度为16字节(AES-128)、24字节(AES-192)或32字节(AES-256)
    key = ws_token_key  # 从配置文件读取的16字节密钥
    if len(key) not in [16, 24, 32]:
        raise ValueError("AES密钥长度必须为16、24或32字节")

    # 获取所有cookies
    cookies = driver.get_cookies()
    if not cookies:
        raise ValueError("未获取到任何cookies")
    # 使用第一个cookie的名称（实际应根据系统需求修改）
    cookie_name = cookies[0]['name']
    data = f"47;{cookie_name};zh_CN".encode("utf-8")
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(data, AES.block_size))
    token = base64.b64encode(encrypted).decode('utf-8')
    print("WS连接令牌:", token)

        # 循环等待
    print(f"\n等待 {loop_interval} 秒后执行下一次循环...")
    time.sleep(loop_interval)
  except KeyboardInterrupt:
        print("\n用户中断程序，退出循环...")
        continue_running = False
  finally:
    driver.quit()
