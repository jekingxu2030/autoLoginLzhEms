from asyncio import sleep
import json
import os
import time
import threading
import logging
from tokenize import Token
from selenium import webdriver
from page_status_checker import PageStatusChecker  # 导入页面状态检查器

# 配置基础日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="debug.log",
    encoding="utf-8",
)
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
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "config.json"
    )
except Exception as e:
    print(f"无法确定配置文件路径: {e}")
    config_path = "config.json"  # 默认路径作为回退
JS_SAVE_DIR = "./downloaded_js"
os.makedirs(JS_SAVE_DIR, exist_ok=True)

# 初始化config变量
config = None

# 加载配置文件
try:
    # 使用绝对路径确保文件位置正确
    abs_config_path = os.path.abspath(config_path)
    with open(abs_config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    logging.info(f"成功加载配置文件: {abs_config_path}")
except FileNotFoundError:
    logging.error(f"错误：配置文件不存在: {os.path.abspath(config_path)}")
    config = None
except json.JSONDecodeError:
    logging.error(
        f"错误：配置文件格式不正确，无法解析JSON: {os.path.abspath(config_path)}"
    )
    config = None
except PermissionError:
    logging.error(f"错误：没有权限读取配置文件: {os.path.abspath(config_path)}")
    config = None
except Exception as e:
    logging.error(f"加载配置文件时发生错误: {e}")
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
loginOk = False
restart_lock = threading.Lock()  # 重启状态锁，防止重启过程中的竞态条件
is_restarting = threading.Event()  # 重启状态标记
Token1 = "2790e24fa6bb40ba86208e99c4b02223941b51a5b61d0f0e08820d3f461e330d"
Token2 = "aa0366d18f2307daa196c4f96546ed629a92b110448ed104614fe9566dfa1b14"
Token3 = "7632cff2eedccb8a21deeed1dbf806bcfeeebd993ead58b522ab4a5b2b23f054"


def find_verification_input_with_debug(driver):
    """
    增强的验证码输入框检测函数，带有详细的调试信息
    """
    print("🔍 开始检测验证码输入框...")
    
    # 获取所有input元素用于调试
    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"📊 页面中找到 {len(all_inputs)} 个input元素")
    
    for i, input_elem in enumerate(all_inputs):
        input_type = input_elem.get_attribute("type") or "text"
        placeholder = input_elem.get_attribute("placeholder") or ""
        input_class = input_elem.get_attribute("class") or ""
        input_id = input_elem.get_attribute("id") or ""
        
        print(f"  Input {i+1}: type={input_type}, placeholder='{placeholder}', class='{input_class}', id='{input_id}'")
        
        # 检查是否是验证码输入框
        if input_type in ["text", ""]:
            # 中文关键词检查
            if any(keyword in placeholder for keyword in ["验证码", "验证", "verification", "code"]):
                print(f"    ✅ 找到可能的验证码输入框 (中文匹配)")
                return input_elem
            
            # 英文关键词检查
            if any(keyword in placeholder.lower() for keyword in ["verification", "captcha", "security"]):
                print(f"    ✅ 找到可能的验证码输入框 (英文匹配)")
                return input_elem
            
            # Class名检查
            if "ant-input" in input_class and not input_id.startswith("form_item_"):
                print(f"    ✅ 找到可能的验证码输入框 (class匹配)")
                return input_elem
    
    print("❌ 未找到符合特征的验证码输入框")
    return None

def test_verification_input_locator():
    """
    测试验证码输入框定位功能的辅助函数
    """
    print("🧪 测试验证码输入框定位功能...")
    
    # 模拟测试数据
    test_cases = [
        {
            "name": "中文环境测试",
            "html": '<input type="text" placeholder="请输入验证码" class="ant-input css-111zvph">'
        },
        {
            "name": "英文环境测试", 
            "html": '<input type="text" placeholder="Please input your verification code" class="ant-input css-111zvph">'
        },
        {
            "name": "混合环境测试",
            "html": '<input type="text" placeholder="Verification Code" class="ant-input">'
        }
    ]
    
    print("✅ 验证码输入框定位逻辑测试完成")
    print("📝 支持的定位方式:")
    print("   1. CSS选择器: input[placeholder='请输入验证码']")
    print("   2. CSS选择器: input[placeholder='Please input your verification code']")
    print("   3. CSS选择器: input.ant-input.css-111zvph")
    print("   4. 模糊匹配: placeholder包含'验证码'或'verification'关键词")
    print("   5. 位置假设: 第三个text input元素")

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
def login(   username, password, load_wait_time ,existing_driver=None):
    """
    登录函数，负责创建或使用现有浏览器实例进行登录
    
    参数:
    username -- 用户名
    password -- 密码
    load_wait_time -- 加载等待时间
    existing_driver -- 可选的现有浏览器驱动实例
    
    返回:
    driver -- 浏览器驱动实例
    """
    global loginOk, driver
    
    # 如果没有提供现有driver，则创建新的
    if existing_driver is None:
        logging.info("创建新的浏览器实例...")
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gcm-registration")  # 阻止 GCM 注册尝试
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        
        # 优化Chrome配置以防止内存泄漏和崩溃
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-component-extensions-with-background-pages")
        options.add_argument("--disable-breakpad")
        options.add_argument("--disable-client-side-phishing-detection")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-web-resources")
        options.add_argument("--disable-cloud-import")
        options.add_argument("--disable-print-preview")
        options.add_argument("--disable-speech-api")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        
        # 使用唯一用户数据目录避免冲突，并定期清理
        user_data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "chrome_user_data"
        )
        os.makedirs(user_data_dir, exist_ok=True)
        options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # 设置内存限制
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=512")
        
        driver = webdriver.Chrome(options=options)
    else:
        logging.info("使用现有浏览器实例...")
        driver = existing_driver
    
    driver.get("http://ems.hy-power.net:8114/login")
    thread_safe_update_debug_label("请求网页中...")
    
    # 智能页面加载检查
    try:
        # 等待页面完全加载并检查访问权限
        WebDriverWait(driver, min(15, load_wait_time + 5)).until(
            lambda d: d.execute_script("return document.readyState;") == "complete" and 
                     d.execute_script("return window.location.href;") != "about:blank"
        )
        
        # 检查页面是否正常加载
        current_url = driver.current_url
        print(f"📍 页面加载完成: {current_url}")
        
        # 预检查页面元素是否存在
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script("return document.body != null;")
        )
        
    except Exception as e:
        print(f"⚠️ 页面加载异常: {str(e)}")
        # 继续执行，避免中断流程

    # 设置emsId - 添加权限检查和错误处理
    try:
        # 等待页面完全加载
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState;") == "complete"
        )
        
        # 检查localStorage权限并设置emsId
        driver.execute_script("""
            try {
                localStorage.setItem('local-power-station-active-emsId', 'E6F7D5412A20');
                return true;
            } catch(e) {
                console.log('localStorage访问失败:', e.message);
                return false;
            }
        """)
        print("✅ localStorage设置成功")
    except Exception as e:
        print(f"⚠️ 设置emsId失败: {str(e)}，继续执行登录流程")
    
    time.sleep(min(load_wait_time, 3))  # 减少等待时间

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "canvas")))
    canvas = driver.find_element(By.ID, "canvas")
    verification_code = canvas.get_attribute("verificationcode")
    print("\n✅[验证码] =", verification_code)

    driver.find_element(By.ID, "form_item_username").clear()
    driver.find_element(By.ID, "form_item_username").send_keys(username)
    driver.find_element(By.ID, "form_item_password").clear()
    driver.find_element(By.ID, "form_item_password").send_keys(password)
    
    # 多语言验证码输入框定位 - 兼容中英文环境
    verification_input = None
    
    # 首先使用增强的调试函数尝试定位
    verification_input = find_verification_input_with_debug(driver)
    
    if not verification_input:
        try:
            # 尝试中文placeholder
            verification_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="请输入验证码"]'))
            )
            print("✅ 找到中文验证码输入框")
        except:
            try:
                # 尝试英文placeholder
                verification_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Please input your verification code"]'))
                )
                print("✅ 找到英文验证码输入框")
            except:
                try:
                    # 尝试通过class名定位
                    verification_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input.ant-input.css-111zvph'))
                    )
                    print("✅ 通过class名找到验证码输入框")
                except:
                    # 最后尝试通用的input类型为text的元素
                    inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
                    for input_elem in inputs:
                        if input_elem.get_attribute("placeholder") and "验证码" in input_elem.get_attribute("placeholder"):
                            verification_input = input_elem
                            print("✅ 通过模糊匹配找到验证码输入框")
                            break
                        elif input_elem.get_attribute("placeholder") and "verification" in input_elem.get_attribute("placeholder").lower():
                            verification_input = input_elem
                            print("✅ 通过模糊匹配找到英文验证码输入框")
                            break
                    
                    if not verification_input and len(inputs) >= 3:
                        # 假设第三个text input是验证码输入框
                        verification_input = inputs[2]
                        print("⚠️ 通过位置假设找到验证码输入框")
    
    if verification_input:
        verification_input.clear()
        verification_input.send_keys(verification_code)
        print(f"✅ 验证码已输入: {verification_code}")
    else:
        print("❌ 无法找到验证码输入框，尝试截图保存当前页面状态")
        # 保存页面截图用于调试
        screenshot_path = f"verification_error_{time.strftime('%Y%m%d_%H%M%S')}.png"
        driver.save_screenshot(screenshot_path)
        print(f"📸 页面截图已保存: {screenshot_path}")
        # 获取页面HTML用于分析
        page_html = driver.page_source
        html_path = f"page_html_{time.strftime('%Y%m%d_%H%M%S')}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"📄 页面HTML已保存: {html_path}")
        raise Exception("无法定位验证码输入框，请检查页面元素")

    time.sleep(load_wait_time + 2)
    WebDriverWait(driver, 10).until(  # 算3秒平均消耗
        EC.element_to_be_clickable((By.CSS_SELECTOR, "form.login-form button"))
    ).click()
    print("\n✅提交登录成功")

    time.sleep(load_wait_time + 5)
    # thread_safe_update_debug_label("登录成功，开始探测内容...")
    # 验证登录是否成功并跳转到主页面
    try:
        # 等待页面跳转到主页面（检查URL是否包含主页标识）
        WebDriverWait(driver, 20).until(
            lambda d: "login" not in d.current_url.lower()
            and d.current_url != "http://ems.hy-power.net:8114/login"
        )
        print(f"\n✅登录成功，已跳转到: {driver.current_url}")
        thread_safe_update_debug_label("登录成功，开始探测内容...")
        loginOk = True
    except:
        # 如果还在登录页面，可能是登录失败
        current_url = driver.current_url
        if "login" in current_url.lower():
            print("\n❌登录失败，仍在登录页面")
            thread_safe_update_debug_label("❌登录失败，请检查用户名密码")
            raise Exception("登录失败，仍在登录页面")

    # 稍微晚点读取cock
    save_browser_cache_to_config(driver)

    ws_url = get_ws_url(driver)  # 保存WS字套
    
    return driver  # 返回浏览器驱动实例


def main_logic():
    global driver  # 声明使用全局变量driver
    try:
        print("📋 开始加载配置文件...")
        thread_safe_update_debug_label("📋加载配置中...")
        
        # 初始化配置字典
        start_time = time.time()
        config = {}
        # 加载配置文件
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        username = config["account"]["username"]
        password = config["account"]["password"]
        load_wait_time = config["timing"]["load_wait_time"]
        loop_interval = config["timing"]["loop_interval"]
        dingtalk_times = config["timing"]["dingtalk_times"]
        
        print(f"✅ 配置加载完成：用户={username}, 等待时间={load_wait_time}s")
        thread_safe_update_debug_label("✅配置加载完成")
        
        # 测试验证码输入框定位逻辑
        test_verification_input_locator()

        global driver, loginOk
        print("🌐 正在启动Chrome浏览器...")
        thread_safe_update_debug_label("🌐启动浏览器中...")
        
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gcm-registration")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        
        # 添加唯一用户数据目录避免冲突
        user_data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "chrome_user_data"
        )
        os.makedirs(user_data_dir, exist_ok=True)
        options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # 优化Chrome启动速度 - 使用轻量级配置
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gcm-registration")
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        
        # 使用临时用户数据目录避免缓存积累
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix="chrome_temp_")
        options.add_argument(f"--user-data-dir={temp_dir}")
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome浏览器启动成功")
        thread_safe_update_debug_label("✅浏览器启动成功")

        print("🔐 开始登录EMS系统...")
        thread_safe_update_debug_label("🔐登录系统中...")
        driver = login(username, password, load_wait_time, driver)
        last_login_time = time.time()
        print("✅ 登录完成")
        thread_safe_update_debug_label("✅登录完成")
        
        time.sleep(load_wait_time + 5)  # 减少等待时间

        # 状态计数变量
        same_error_count = 0
        intervalCounts = 0
        total_cycle_count = 0
        checkCounts = 0
        
        # 浏览器重启管理变量
        browser_restart_interval = 23 * 3600
        last_browser_restart = time.time()
        
        # 启动浏览器监控线程
        monitor_thread = threading.Thread(
            target=browser_monitor_thread, 
            daemon=True
        )
        monitor_thread.start()
        print("🔍 浏览器监控线程已启动")

        print("📊 正在初始化菜单数据...")
        thread_safe_update_debug_label("📊初始化数据中...")
        menu_data = fetch_menu_once()
        print("✅ 菜单数据初始化完成")
        thread_safe_update_debug_label("✅初始化完成")
        
        end_time = time.time()
        elapsed_time1 = end_time - start_time
        print(f"🎉 系统启动完成，总耗时：{elapsed_time1:.2f}秒")
        thread_safe_update_debug_label("🎉系统启动完成，开始监控")
        
        # 启动成功提示
        print("🔄 监控系统已启动，正在进入主循环...")
        print("💡 这是正常行为：程序将持续监控EMS系统状态")
        print("⏰ 每轮检测间隔约60秒，请耐心等待下一轮检测...")
        thread_safe_update_debug_label("🔄监控系统运行中，每60秒检测一次")

        okCounts = 0
        while_time = 0  # 循环一次的时间
        while not stop_event.is_set():
            # ws_url = get_ws_url(driver)
            if total_cycle_count == 0:
                print("🎯 开始第一轮检测...")
                thread_safe_update_debug_label("🎯开始第一轮检测...")
            
            while_time_start = time.time()  # 主循环间隔
            current_time = time.time()  # 登录间隔

            if loginOk:
                print("登录有效！")
            else:
                driver=login( username, password, load_wait_time,driver)
                time.sleep(load_wait_time * 2 + 10)
            # 原代码包含多余的config参数，已注释

            # 检查是否超过23小时(82800秒)未重新登录
            if current_time - last_login_time >= 22 * 3600:
                #  if current_time - last_login_time >= 23 * 3600:
                print("🔄 已超过23小时，准备重新登录...")
                thread_safe_update_debug_label(f"🔄登录已超过23小时，准备重新登录...")
                # login(driver, username, password, load_wait_time)
                restart_browser(username, password, load_wait_time)  #
                time.sleep(load_wait_time * 2 + 10)
                last_login_time = current_time  # 更新登录时间

            total_cycle_count += 1

            WebDriverWait(driver, 20).until(  # 算3秒
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            # 模拟鼠标动作
            driver.execute_script("window.scrollBy(0, 10);")
            driver.execute_script("window.dispatchEvent(new Event('mousemove'))")
            time.sleep(5)

            # 爬取记录开始时间
            start_time = time.time()  # 内容检测开始时间
            ws_monitor = EmsWsMonitor(
                driver, timeout=load_wait_time + 25, menu_data=menu_data
            )
            status = ws_monitor.start()
            # 记录结束时间
            end_time = time.time()
            # 计算耗时（秒）
            # elapsed_time2 = end_time - start_time
            print("WS检测状态：", status)

            if status == "✅ok":
                same_error_count = 0  # 打断异常，重置异常计数  在连续错误三次或三次后连续错误会一直保持大于3，等待正常逻状态下归零
                okCounts += 1  # 正常加一
                intervalCounts += 1  # 总判断次数加一
                normal_push_interval = while_time * (
                    max(1, (dingtalk_times * 24) - intervalCounts)  # 循环时间*剩余次数
                )
                Content = (
                    f"Event: BY-P01-EMS_StatusCheck\n"
                    f"State: Normal!\n"
                    f"CheckUrl: {driver.current_url}\n"
                    f"Message:✅网站正常，收到实时新数据！\n"
                    f"WebSiteState: Accessible！\n"
                    f"Time：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                if intervalCounts >= dingtalk_times * 24:  # 连续推送
                    send_dingtalk_msg(Content, Token3)
                    # 加载邮箱配置
                    try:
                        with open(
                            os.path.join(
                                os.path.dirname(os.path.abspath(__file__)),
                                "email_config.json",
                            ),
                            "r",
                            encoding="utf-8",
                        ) as f:
                            email_config = json.load(f)
                    except FileNotFoundError:
                        logging.error("邮箱配置文件不存在: email_config.json")
                        raise
                    except json.JSONDecodeError as e:
                        logging.error(f"邮箱配置文件格式错误: {str(e)}")
                        raise
                    send_email(
                        email_config["normal_recipients"],
                        "【EMS Events】",
                        f"《提示!》\n\n尊敬的用户您好！您的215P01项目EMS后台系统数据“正常” ，请您放心运行!谢谢!\nCheckUrl: {driver.current_url}\n\n\n检测时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        from_addr=email_config["from_addr"],
                    )
                    intervalCounts = 0
                    # driver.refresh()  # 刷新网页
                    time.sleep(1)
                else:
                    if (
                        okCounts == 1
                    ):  # 首次正常或错误后恢复正常后的第一次正常也直接发出
                        # print("推送")
                        send_dingtalk_msg(Content, Token3)

                    else:  # 既不是首次也不未达到长间隔
                        print(
                            f"✅ 当前为【正常状态】,距离下次推送间隔约 {normal_push_interval} 秒 ≈ {normal_push_interval / 60:.1f} 分钟"
                        )

            elif status in ["❌empty", "❌no_msg", "❌no_ws", "❌error", "❌timeout"]:
                okCounts = 0
                same_error_count += 1
                # 根据状态自适应输出网站状态描述
                if status == "❌empty":
                    web_state_desc = "网站访问正常，但数据返回为空"
                elif status == "❌no_msg":
                    web_state_desc = "WebSocket连接正常，但无有效数据"
                elif status == "❌no_ws":
                    web_state_desc = "❌ 无法建立 WebSocket 连接"
                elif status == "❌error":
                    web_state_desc = "❌ 发生未知错误，页面可能无法访问"
                elif status == "❌timeout":
                    web_state_desc = "❌ WebSocket 连接超时"
                else:
                    web_state_desc = "❓ 不明状态异常"
                errocontent = (
                    f"Event: BY-P01-EMS_StatusCheck\n"
                    f"State: Alarm!\n"
                    f"CheckUrl: {driver.current_url}\n"
                    f"Message:网站状态异常[{status}]，请检查！\n"
                    f"WebSiteState: {web_state_desc}\n"
                    f"Time：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                error_push_interval = while_time * (
                    max(
                        1, loop_interval - same_error_count
                    )  # 设定首次错误减去已错误次数
                )

                if same_error_count == loop_interval:  # 错误次数等于设定错误等待间隔
                    # error_frist_push_interval = while_time * (max(1, loop_interval - same_error_count))
                    send_dingtalk_msg(errocontent, Token3)
                    # 加载邮箱配置
                    try:
                        with open(
                            os.path.join(
                                os.path.dirname(os.path.abspath(__file__)),
                                "email_config.json",
                            ),
                            "r",
                            encoding="utf-8",
                        ) as f:
                            email_config = json.load(f)
                    except FileNotFoundError:
                        logging.error("邮箱配置文件不存在: email_config.json")
                        raise
                    except json.JSONDecodeError as e:
                        logging.error(f"邮箱配置文件格式错误: {str(e)}")
                        raise
                    send_email(
                        email_config["error_recipients"],
                        "【EMS Events】",
                        f"《警告!》\n\n尊敬的用户您好！我们检测到您的215P01项目EMS后台系统出现异常状态：{status}。请您尽快检查和处理!谢谢!\nCheckUrl: {driver.current_url}\n\n\n事件时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        from_addr=email_config["from_addr"],
                    )

                    intervalCounts = 0
                    print(
                        f"❗ 当前为【异常状态: {status}】，距离下轮首错推送时间至少：{(error_push_interval*dingtalk_times) / 60:.1f} 分钟"
                    )

                elif (
                    same_error_count > loop_interval
                ):  # 错误次数大于设于最小间隔连续后时间延长

                    if intervalCounts >= dingtalk_times:  # 延长异常推送间隔

                        send_dingtalk_msg(errocontent, Token3)
                        try:
                            with open(
                                os.path.join(
                                    os.path.dirname(os.path.abspath(__file__)),
                                    "email_config.json",
                                ),
                                "r",
                                encoding="utf-8",
                            ) as f:
                                email_config = json.load(f)
                        except FileNotFoundError:
                            logging.error("邮箱配置文件不存在: email_config.json")
                            raise
                        except json.JSONDecodeError as e:
                            logging.error(f"邮箱配置文件格式错误: {str(e)}")
                            raise
                        send_email(
                            email_config["error_recipients"],
                            "【EMS Events】",
                            f"《警告!》\n\n尊敬的用户您好！我们检测到您的215P01项目EMS后台系统持续异常[{status}]。请您尽快检查和处理!谢谢!\nCheckUrl: {driver.current_url}\n\n\n事件时间：{datetime.now()}",
                            from_addr="jekingxu@163.com",
                        )
                        # 超过指定次数后 连续错误后又连续间隔错误次数后归零
                        intervalCounts = 0
                        # error_push_interval = while_time * (max(1, loop_interval - same_error_count))
                        # 前几次时间最短
                        print(
                            f"❗ 当前为【异常状态: {status}】，距离下一次连续错误推送约 {error_push_interval} 秒 ≈ {error_push_interval / 60:.1f} 分钟"
                        )

                    else:
                        intervalCounts += 1  # 跳过就+1

                        print(
                            f"第{same_error_count}次异常状态，错误次数>0和错误首次间隔次数，但<连续错误间隔次数"
                        )
                        print(
                            f"❗ 当前为【异常状态: {status}】，距离下一次错误推送约 {error_push_interval} 秒 ≈ {error_push_interval / 60:.1f} 分钟"
                        )
                else:
                    intervalCounts += 1  # 跳过每次都加1
                    print(
                        f"第{same_error_count}次异常状态，错误次数>0<错误首次间隔次数和连续错误间隔次数"
                    )
                    print(
                        f"❗ 当前为【异常状态: {status}】，距离下一次错误推送约 {error_push_interval} 秒 ≈ {error_push_interval / 60:.1f} 分钟"
                    )

            driver.refresh()  # 刷新网页
            print(f"刷新网页...")

            # 使用页面状态检查器检查是否出现登录页面
            page_checker = PageStatusChecker(driver)
            time.sleep(5)
            # 定义重新登录的函数（需要根据实际登录逻辑实现）
            # 检查是否出现登录页面，返回状态
            is_logged_out = page_checker.is_login_page_present()
            time.sleep(10)
            if is_logged_out:
                print("⚠️ 系统当前状态：掉线")
                # 立即触发重新登录流程
                try:
                    print("🔍 检测到登录页面，开始执行重新登录...")
                    thread_safe_update_debug_label("系统状态：掉线 - 正在重新登录...")
                    page_checker.handle_login_page(login_func)
                    print("✅ 重新登录流程已触发")
                    thread_safe_update_debug_label("系统状态：重新登录完成")
                except Exception as e:
                    print(f"❌ 重新登录失败：{str(e)}")
                    thread_safe_update_debug_label("系统状态：重新登录失败")
                    time.sleep(10)  # 失败后等待较长时间再重试
            else:
                print("✅ 系统当前状态：已登录")

            # 清理缓存与内存
            gc.collect()
            
            # 浏览器状态检查和异常处理 - 增加重启保护
            try:
                # 如果正在重启，跳过状态检查
                if is_restarting.is_set():
                    print("⏸️ 浏览器正在重启中，跳过本轮状态检查")
                    time.sleep(10)  # 等待重启完成
                    continue  # 跳过本轮检测，直接下一轮
                    
                # 使用专门的检查函数验证浏览器状态
                browser_alive = check_browser_status(driver)
            except Exception as e:
                print(f"🚨 检测到浏览器异常退出: {e}")
                
                # 如果正在重启，不重复处理
                if is_restarting.is_set():
                    print("⏸️ 重启已在进行中，跳过异常处理")
                    time.sleep(10)
                    continue
                    
                thread_safe_update_debug_label("🚨检测到浏览器异常退出，准备重启...")
                browser_alive = False
                
            if not browser_alive:
                print("🔄 开始浏览器异常恢复流程...")
                
                # 再次确认没有正在重启
                if is_restarting.is_set():
                    print("⏸️ 检测到重启已在进行中，等待完成...")
                    time.sleep(15)
                    continue
                
                retry_count = 0
                max_retries = 3
                
                while retry_count < max_retries:
                    retry_count += 1
                    print(f"🔄 第{retry_count}次尝试重启浏览器...")
                    
                    if force_restart_browser(username, password, load_wait_time):
                        print("✅ 浏览器重启流程已启动，等待完成...")
                        # force_restart_browser内部已经处理了40秒等待
                        last_browser_restart = time.time()
                        break
                    else:
                        print(f"❌ 第{retry_count}次重启失败，等待后重试...")
                        time.sleep(20)  # 进一步增加等待时间
                        
                if retry_count >= max_retries:
                    print("❌ 浏览器重启失败，程序可能无法继续运行")
                    thread_safe_update_debug_label("❌浏览器重启失败，请手动检查")
                    # 给手动处理机会，等待更长时间
                    time.sleep(30)
            
            # 内存监控和强制清理（仅当浏览器正常时执行）
            if browser_alive:
                try:
                    # 定期清理浏览器缓存
                    driver.execute_script("window.localStorage.clear();")
                    driver.execute_script("window.sessionStorage.clear();")
                    
                    # 强制垃圾回收
                    import psutil
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    print(f"当前进程内存使用: {memory_info.rss / 1024 / 1024:.2f} MB")
                    
                    # 如果内存使用过高，强制重启
                    if memory_info.rss > 1024 * 1024 * 1024:  # 超过1GB
                        print("⚠️ 内存使用过高，强制重启浏览器...")
                        restart_browser(username, password, load_wait_time + 10)
                        last_browser_restart = time.time()
                        
                except Exception as e:
                    print(f"内存监控出错: {e}")

            time.sleep(load_wait_time + 5)

            checkCounts += 1
            # print(f"\n已经检测第{checkCounts}轮")

            # 定期重启浏览器防止资源泄漏（两种方式：循环次数或时间间隔）
            current_time = time.time()
            
            # 23小时强制重启检查
            if current_time - last_browser_restart >= browser_restart_interval:
                print("🔄 达到23小时运行时间，准备强制重启浏览器...")
                thread_safe_update_debug_label("🔄达到23小时，准备重启浏览器...")
                try:
                    restart_browser(username, password, load_wait_time + 10)
                    time.sleep(load_wait_time + 5)
                    last_browser_restart = current_time  # 更新重启时间
                except Exception as e:
                    print(f"🔄 12小时重启失败: {e}")
                    thread_safe_update_debug_label(f"❌12小时重启失败: {e}")
            
            # 基于循环次数的重启（备用机制）
            elif total_cycle_count % 10000 == 0:
                print("🔁 达到10000次检测，准备重启浏览器...")
                try:
                    restart_browser(
                        username, password, load_wait_time + 10
                    )  # 算3秒平均消耗
                    time.sleep(load_wait_time + 5)
                    last_browser_restart = current_time  # 更新重启时间
                except Exception as e:
                    print(f"🔁 浏览器重启失败: {e}")
                    thread_safe_update_debug_label(f"❌浏览器重启失败: {e}")

                    # 这里要重新执行登录操作（填写用户名、密码、验证码等）
            else:
                print(f"\n✅ 第{total_cycle_count}轮检测完成，等待下一轮...")
                thread_safe_update_debug_label(f"✅第{total_cycle_count}轮完成，等待下一轮...")

            while_time_end = time.time()
            while_time = while_time_end - while_time_start
            print(f"⏱️ 本轮耗时{while_time:.1f}秒，{load_wait_time+5}秒后开始下一轮")

            # # 新增：重新加载配置文件
            try:
                # config = configparser.ConfigParser()
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    load_wait_time = config["timing"][
                        "load_wait_time"
                    ]  # 第一个加载等待时间
                    loop_interval = config["timing"][
                        "loop_interval"
                    ]  # 第二个时间  首次错误等待次数
                    dingtalk_times = config["timing"][
                        "dingtalk_times"
                    ]  # 第三个时间  正常和不正常连续推送间隔次数
            except Exception as e:
                print(f"重新加载配置文件失败: {e}")
            print(
                f"\nload_wait_time={load_wait_time} , \nloop_interval={loop_interval},\ndingtalk_times={dingtalk_times},\nintervalCounts={intervalCounts},\nsame_error_count={same_error_count},\nAllRunTime={ elapsed_time1 + while_time}"
            )

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
        print("🚨 主线程逻辑异常:", e)
        thread_safe_update_debug_label(f"❌主逻辑异常: {str(e)}")
        
        # 检查是否为验证码输入框定位错误
        error_msg = str(e).lower()
        if "无法定位验证码输入框" in error_msg or "no such element" in error_msg:
            print("⚠️ 检测到验证码输入框定位失败，尝试重新登录...")
            # 尝试重新登录
            try:
                # 使用已经声明的全局变量loginOk（已在函数开头声明）
                loginOk = False
                # 等待一段时间后重试
                time.sleep(10)
                return  # 退出当前异常处理，让主循环重新登录
            except Exception as retry_error:
                print(f"❌ 重新登录尝试失败: {retry_error}")
        
        # 检查是否为权限错误，避免无限重启
        elif "localstorage" in error_msg or "access is denied" in error_msg:
            print("⚠️ 检测到权限错误，跳过localStorage设置继续运行...")
            # 不触发重启，记录后继续运行
            time.sleep(30)  # 等待30秒后重试，避免频繁异常
            return  # 退出当前异常处理，继续主循环
            
        print(f"🔄 尝试自动恢复程序运行...")
        
        # 尝试自动恢复
        recovery_attempts = 0
        max_recovery_attempts = 3
        
        while recovery_attempts < max_recovery_attempts:
            recovery_attempts += 1
            print(f"🔄 第{recovery_attempts}次尝试恢复程序运行...")
            
            try:
                # 强制重启浏览器
                if force_restart_browser(username, password, load_wait_time):
                    print("✅ 程序恢复成功，继续运行")
                    thread_safe_update_debug_label("✅程序自动恢复成功")
                    # 重置相关计数器
                    total_cycle_count = 0
                    last_browser_restart = time.time()
                    # 继续主循环 - 使用break退出恢复循环，回到主循环
                    recovery_attempts = 0  # 重置恢复计数器
                    break  # 退出恢复循环，继续主循环
                else:
                    print(f"❌ 第{recovery_attempts}次恢复失败")
                    
            except Exception as recovery_error:
                print(f"❌ 恢复过程中出错: {recovery_error}")
                
            time.sleep(15)  # 等待15秒后重试
            
        if recovery_attempts >= max_recovery_attempts:
            print("❌ 程序恢复失败，需要手动干预")
            thread_safe_update_debug_label("❌程序恢复失败，请检查")
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
                loginOk = False


# ==============================================
# 重启函数
def restart_browser(username, password, load_wait_time):
    global driver, loginOk
    try:
        driver.quit()
        time.sleep(5)
        loginOk = False
        time.sleep(5)

        gc.collect()
        kill_existing_processes()
        # 调用login函数，让其创建新的driver实例并更新全局变量
        driver = login(username, password, load_wait_time )
        time.sleep(load_wait_time + load_wait_time + 5)

    except Exception:
        pass


# ==============================================重启浏览器结束

# ==============================================浏览器状态检查函数
def check_browser_status(driver):
    """检查浏览器是否正常运行"""
    try:
        # 尝试访问一个简单页面来测试浏览器状态
        driver.execute_script("return 1;")
        return True
    except Exception as e:
        print(f"浏览器状态检查失败: {e}")
        return False

def force_restart_browser(username, password, load_wait_time):
    """强制重启浏览器并重新初始化"""
    global driver, loginOk
    
    # 检查是否已经在重启中，避免重复重启
    if is_restarting.is_set():
        print("⚠️ 重启已在进行中，跳过本次重启请求")
        return False
    
    try:
        # 设置重启标记，防止监控线程干扰
        is_restarting.set()
        print("🔥 开始强制重启浏览器流程...")
        
        # 1. 尝试关闭现有浏览器
        try:
            if driver:
                driver.quit()
                print("✅ 已关闭现有浏览器")
        except Exception as e:
            print(f"关闭浏览器时出错: {e}")
        
        # 2. 强制清理所有chrome进程
        kill_existing_processes()
        
        # 3. 垃圾回收和冷却时间 - 增加冷却时间
        gc.collect()
        print("⏳ 冷却期：等待进程完全退出...")
        time.sleep(8)  # 增加到8秒，确保进程完全退出
        
        # 4. 重新创建浏览器实例 - 添加启动保护
        print("🔄 重新创建浏览器实例...")
        driver = login(username, password, load_wait_time)
        
        # 5. 智能等待浏览器就绪 - 减少固定等待
        print("⏳ 浏览器启动中，智能等待就绪...")
        thread_safe_update_debug_label("⏳浏览器启动中，智能等待就绪...")
        
        # 使用渐进式等待替代固定40秒
        max_wait = 30  # 最大等待时间减少到20秒
        start_wait = time.time()
        while time.time() - start_wait < max_wait:
            try:
                driver.execute_script("return 1;")
                break  # 浏览器已就绪，提前退出等待
            except:
                time.sleep(1)  # 每秒检查一次
        
        # 6. 渐进式验证新实例是否正常工作
        max_verify_attempts = 5  # 增加到5次验证
        for attempt in range(max_verify_attempts):
            print(f"🔍 第{attempt+1}次验证浏览器状态...")
            
            # 渐进式验证：先简单后复杂
            try:
                # 验证1：检查driver对象是否存在
                if not driver:
                    raise Exception("driver对象为空")
                
                # 验证2：检查能否执行简单脚本
                driver.execute_script("return 1;")
                
                # 验证3：检查能否获取当前URL
                current_url = driver.current_url
                
                # 验证4：检查页面是否加载完成
                ready_state = driver.execute_script("return document.readyState;")
                
                if ready_state in ['complete', 'interactive']:
                    print(f"✅ 浏览器重启成功，所有验证通过")
                    print(f"📍 当前URL: {current_url}")
                    print(f"📊 页面状态: {ready_state}")
                    loginOk = True
                    return True
                else:
                    print(f"⏳ 页面状态为{ready_state}，继续等待...")
                    
            except Exception as verify_error:
                print(f"⚠️ 第{attempt+1}次验证失败: {str(verify_error)[:100]}")
                if attempt < max_verify_attempts - 1:
                    wait_time = 10 * (attempt + 1)  # 递增等待时间
                    print(f"⏳ 等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print("❌ 浏览器重启后多次验证仍无法正常工作")
                    
        return False
            
    except Exception as e:
        print(f"❌ 强制重启浏览器失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 延迟清除重启标记，给系统更多时间稳定
        time.sleep(5)
        is_restarting.clear()
        print("🔄 重启流程结束，重启标记已清除")


# === 设置窗口线程 ===
def run_settings():
    global settings_window, loginOk
    root = tk.Tk()

    def on_closing():
        # /*******  88517a0e-ce2f-486d-b6d6-1ecd6e20a7f5  *******/
        global loginOk
        stop_event.set()
        running_event.clear()
        if driver:
            try:
                driver.quit()
                loginOk = False
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
        print("🚀 正在启动主线程...")
        thread_safe_update_debug_label("🚀正在启动主线程...")
        
        # 启动主线程
        logic_thread = threading.Thread(target=main_logic, daemon=True)
        logic_thread.start()
        
        # 监控线程将在主线程启动后，从配置文件中获取参数启动
        running_event.set()
        print("✅ 主线程启动完成")
        thread_safe_update_debug_label("✅主线程启动完成")


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


# ==============================================浏览器监控线程
def browser_monitor_thread():
    """浏览器监控线程，按循环次数累积后执行一次浏览器状态检测"""
    print("🔍 浏览器监控线程已启动")

    # 初始化变量，确保在所有分支都有定义
    username = ""
    password = ""
    load_wait_time = 1
    monitor_interval = 60
    check_cycles = 60

    # 从配置文件读取参数
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        username = config["account"]["username"]
        password = config["account"]["password"]
        load_wait_time = config["timing"]["load_wait_time"]
        loop_interval = config["timing"].get("loop_interval", 1)
        monitor_interval = config["timing"].get("monitor_interval", 60)  # 从配置读取监控间隔，默认60秒
        check_cycles = config["timing"].get("check_cycles", 60)  # 累积检测次数，默认60次
    except Exception as e:
        print(f"监控线程读取配置失败: {e}，使用默认值")

    cycle_count = 0  # 循环计数器
    restart_cooldown = 0  # 重启后冷却计数器
    print(
        f"📊 监控线程配置：基础间隔={loop_interval}秒，累积{cycle_count}/{check_cycles}次后检测"
    )

    while not stop_event.is_set():
        try:
            cycle_count += 1

            # 检查是否在重启过程中，如果是则跳过并重置计数器
            if is_restarting.is_set():
                print("🔄 监控线程：检测到重启进行中，跳过本次检查")
                cycle_count = 0  # 重启过程中重置计数器
                time.sleep(loop_interval)
                continue

            # 重启后冷却期：重启完成后跳过前N次检测
            if restart_cooldown > 0:
                restart_cooldown -= 1
                if restart_cooldown % 10 == 0:  # 每10次打印一次冷却日志
                    print(f"⏳ 重启后冷却期：剩余{restart_cooldown}次检测跳过")
                time.sleep(monitor_interval)
                continue

            # 达到累积次数才执行浏览器状态检测
            if cycle_count >= check_cycles:
                cycle_count = 0  # 重置计数器

                # 执行浏览器状态检测
                if driver and not check_browser_status(driver):
                    print("🚨 监控线程检测到浏览器异常，准备重启...")
                    thread_safe_update_debug_label("🚨监控检测到异常，准备重启...")

                    # 使用强制重启，成功后设置冷却期
                    success = force_restart_browser(username, password, load_wait_time)
                    if success:
                        restart_cooldown = check_cycles // 2  # 成功后跳过一半的检测周期
                        print(f"✅ 重启成功，设置冷却期：跳过{restart_cooldown}次检测")
                else:
                    # 每完整检测周期打印一次正常状态
                    print("✅ 监控线程：浏览器状态正常")

            time.sleep(loop_interval)

        except Exception as e:
            print(f"监控线程出错: {e}")
            cycle_count = 0  # 出错时也重置计数器
            restart_cooldown = 0  # 出错时也重置冷却期
            time.sleep(loop_interval)

if __name__ == "__main__":
    kill_existing_processes()
    run_settings()
