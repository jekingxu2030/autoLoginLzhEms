import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class PageStatusChecker:
    """
    页面状态检查器，用于检测页面是否掉线（出现登录页面）
    """
    def __init__(self, driver):
        """
        初始化页面状态检查器
        :param driver: Selenium WebDriver实例
        """
        self.driver = driver
        # 配置日志
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            filename="debug.log",
            encoding="utf-8",
        )

    def is_login_page_present(self, timeout=10):
        """
        检查是否存在登录页面（通过检测login-page类的div元素）
        :param timeout: 等待超时时间（秒）
        :return: 如果存在登录页面返回True，否则返回False
        """
        try:
            # 检查是否存在类名为login-page的div元素
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "login-page"))
            )
            self.logger.info("检测到登录页面，页面可能已掉线")
            print("❌ 检测到登录页面，页面可能已掉线")
            return True
        except TimeoutException:
            self.logger.info("未检测到登录页面，登录未掉线！")
            print("✅ 未检测到登录页面，登录未掉线！")
            return False

    def handle_login_page(self, login_func):
        """
        处理登录页面：如果检测到登录页面，则执行登录函数
        :param login_func: 登录函数，无参数
        :return: 如果执行了登录返回True，否则返回False
        """
        if self.is_login_page_present():
            self.logger.info("准备执行重新登录")
            print("🔄 准备执行重新登录...")
            try:
                login_func()
                self.logger.info("重新登录成功")
                print("✅ 重新登录成功")
                return True
            except Exception as e:
                self.logger.error(f"重新登录失败: {str(e)}")
                print(f"❌ 重新登录失败: {e}")
                return False
        return False