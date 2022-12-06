import json
import logging
import queue
import signal
import sys
import time
from logging import FileHandler
from logging import LogRecord
from logging import StreamHandler
from pathlib import Path

import requests
import selenium
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromiumService
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

CONF_FILE = './conf/user.json'  # 配置文件位置
RUIJIE_LOGIN_URL = 'http://172.30.30.72/'  # 锐捷登录地址
NETWORK_CHECK_TIMEOUT = 10  # 网络连通性测试超时
NETWORK_CHECK_INTERVAL = 30  # 网络连通性测试间隔
RUIJIE_LOGIN_INTERVAL = 600  # 锐捷登录最小间隔
ALARM_INTERVAL = 10
SCRIPT_TIMEOUT = 30  # 浏览器执行脚本超时
PAGE_LOAD_TIMEOUT = 300  # 浏览器加载页面超时
IMPLICIT_WAIT_TIMEOUT = 300  # 浏览器隐式等待超时
NETWORK_CHECK_URL = 'http://www.msftconnecttest.com/connecttest.txt'  # 网络连通性测试超时地址
NETWORK_CHECK_CONTENT = b'Microsoft Connect Test'  # 网络连通性测试内容
LOG_LEVEL = logging.INFO  # 控制台日志级别
LOG_FILE_LEVEL = logging.DEBUG  # 日志文件日志级别
LOG_FILE_FORMAT = '%(levelname)s:%(asctime)s:%(name)s:%(message)s'
LOG_FILE = 'logs/ruijie-login.log'  # 日志文件位置
DRIVER_DIR = '.'  # 驱动程序位置
DRIVER_CHECK_INTERVAL = 1800
DEBUG = False  # 为 False 时不会显示浏览器窗口

logger = logging.getLogger()


# def my_firefox_options():
#     options = ChromeOptions()
#     firefox_profile = FirefoxProfile()
#     firefox_profile.set_preference("dom.webdriver.enabled", False)
#     firefox_profile.set_preference("permissions.default.image", 2)
#     firefox_profile.set_preference("permissions.default.stylesheet", 2)
#
#     options.add_argument('--disable-gpu')  # 禁用 GPU 加速
#     options.add_argument('--window-size=1920x1080')  # 设置浏览器分辨率（窗口大小）
#     options.add_argument('--private')
#     if not DEBUG:
#         options.add_argument('--headless')  # 无界面
#
#     options.accept_insecure_certs = True
#     options.timeouts = {"implicit": IMPLICIT_WAIT_TIME_OUT * 1000,
#                         "pageLoad": PAGE_LOAD_TIMEOUT * 1000,
#                         "script": SCRIPT_TIMEOUT * 1000}
#     return options


# 日志文件处理器
class MyLogFileHandler(FileHandler):
    def __init__(self, filename: str):
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        super().__init__(filename, encoding='utf-8')
        self.setLevel(LOG_FILE_LEVEL)
        self.setFormatter(logging.Formatter(LOG_FILE_FORMAT))


# 日志输出流处理器
class MyLogStreamHandler(StreamHandler):
    def __init__(self):
        super().__init__(sys.stdout)
        self.setLevel(LOG_LEVEL)

    def format(self, record: LogRecord) -> str:
        # 为日志增加颜色
        match record.levelno:
            case logging.DEBUG:
                prefix = '\033[32m'
                suffix = '\033[0m'
            case logging.WARNING:
                prefix = '\033[33m'
                suffix = '\033[0m'
            case logging.ERROR:
                prefix = '\033[31m'
                suffix = '\033[0m'
            case logging.FATAL:
                prefix = '\033[1m\033[31m'
                suffix = '\033[0m'
            case _:
                prefix = ''
                suffix = ''
        return f'{prefix}{super().format(record)}{suffix}'


# 用户信息类
class User:
    username: str
    password: str
    userType: int

    def __init__(self, user_name='', passwd='', user_type=0):
        self.username = user_name
        self.password = passwd
        self.userType = user_type  # 0 为教师 1 为学生 2 为临时人员
        if user_type not in [0, 1, 2]:
            logger.error('Illegal user_type')


class MyChromeControl:
    options: ChromeOptions
    driver: ChromiumDriver | None = None
    logger: logging.Logger
    driver_path: str | None

    def __init__(self):
        self.logger = logging.getLogger('MyChromeControl')
        self.options = my_chrome_options()
        self.driver_path = None
        self.driver = None

    def __del__(self):
        self.quit()

    def start_browser(self):
        if self.driver_path is None:
            self.install_driver()

        self.logger.info('Start browser')

        self.driver = webdriver.Chrome(service=ChromiumService(self.driver_path), options=self.options)
        self.logger.info(f'Browser name: {self.driver.name}')

    # 安装驱动，如果驱动已经安装，直接返回驱动路径
    def install_driver(self):
        for browser in [ChromeType.GOOGLE, ChromeType.CHROMIUM, ChromeType.MSEDGE, ChromeType.BRAVE]:
            driver_manager = ChromeDriverManager(path=DRIVER_DIR, chrome_type=browser)
            if driver_manager.driver.get_browser_version() is None:
                continue

            self.logger.info(f'Use browser: {browser}')
            break

        if driver_manager is None:
            self.logger.critical('No supported browsers found')
            sys.exit(-1)

        self.driver_path = driver_manager.install()
        self.logger.debug(f'Driver path: {self.driver_path}')

    # 退出浏览器
    def quit(self):
        self.logger.debug('Quit')
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

    def find_element_by_id(self, value: str) -> WebElement:
        self.logger.debug(f'Find element by f{value}')
        elem = self.driver.find_element(By.ID, value)
        if elem is None:
            raise NoSuchElementException(f"Cannot locate relative element with: {value}")
        return elem

    def open_page(self, url: str):
        self.logger.debug(f'Open Page: {RUIJIE_LOGIN_URL}')
        self.driver.get(url)

    def submit_login_info(self, user: User):
        # 找用户名输入框。
        username = self.find_element_by_id("username")
        username.clear()
        username.send_keys(user.username)

        # 这是个安全机制，密码框是隐藏的。要点一下 pwd_tip 密码框才会出来。
        password_tip = self.find_element_by_id("pwd_tip")
        password_tip.click()

        # 找密码输入框。
        password = self.find_element_by_id("pwd")
        password.clear()
        password.send_keys(user.password)

        # 找连接类型选择框。
        select = self.find_element_by_id("selectDisname")
        select.click()

        # 找用户类型。
        type_id = ['_service_0', '_service_1', '_service_2']
        student = self.find_element_by_id(type_id[user.userType])
        student.click()

        # 找登录按钮。
        login_button = self.find_element_by_id("loginLink_div")
        login_button.click()

    # 下线
    def logout(self):
        self.logger.debug(f'Logout')
        to_log_out = self.find_element_by_id("toLogOut")
        to_log_out.click()
        alert: Alert = WebDriverWait(self.driver, IMPLICIT_WAIT_TIMEOUT).until(expected_conditions.alert_is_present())
        alert.accept()

    def automatic_login(self, user: User):
        if self.driver is None:
            self.start_browser()

        result = False
        try:
            self.open_page(RUIJIE_LOGIN_URL)
            self.logger.debug(f'Page title: {self.driver.title}')

            if self.driver.title == '登录成功':
                self.logout()
                re_login = self.find_element_by_id("offlineDiv")  # 重新登录
                re_login.click()

            self.submit_login_info(user)

            try:
                is_login: bool = WebDriverWait(self.driver, IMPLICIT_WAIT_TIMEOUT).until(
                    expected_conditions.title_is('登录成功'))
                if is_login:
                    result = True
            except TimeoutException:
                pass

        except WebDriverException as err:
            logger.warning(err)

        self.driver.close()
        return result


class MyApp:
    eventQue: queue.Queue
    user: User
    lastCheckNetwork: int
    lastCheckDriver: int
    lastLogin: int

    def __init__(self):
        self.eventQue = queue.Queue()
        self.lastCheckNetwork = 0
        self.lastLogin = 0

    def sig_handler(self, signum, _frame):
        sig_name = signal.Signals(signum).name
        logger.info(f'Signal handler called with signal {sig_name}({signum})')
        self.eventQue.put('EXIT')

    def alarm_handler(self, _signum, _frame):
        self.eventQue.put('ALARM')

    def check_driver_tick(self):
        logger.info('Check driver')
        now = int(time.time())
        if now - self.lastCheckDriver < DRIVER_CHECK_INTERVAL:
            return
        self.lastCheckDriver = now
        MyChromeControl().install_driver()

    def check_network_tick(self):
        now = int(time.time())
        if now - self.lastCheckNetwork < NETWORK_CHECK_INTERVAL:
            return
        self.lastCheckNetwork = now

        logger.info('Check network')
        if not is_network_connect():
            logger.info('Network is unavailable')
            if is_ruijie_connect():
                self.ruijie_login()
            else:
                logger.warning('Ruijie website is unavailable')
        else:
            logger.info('Network is OK')
            self.check_driver_tick()
            if DEBUG:
                self.ruijie_login()
                # input()

    def ruijie_login(self):
        now = int(time.time())
        if now - self.lastLogin < RUIJIE_LOGIN_INTERVAL:
            return
        self.lastLogin = now

        control = MyChromeControl()
        if control.automatic_login(self.user):
            logger.info('Ruijie login success')
        else:
            logger.warning('Ruijie login fail')
        control.quit()

    def event_loop(self, timeout: float | None = None):
        while True:
            match self.eventQue.get(timeout=timeout):
                case 'EXIT':
                    break
                case 'ALARM':
                    self.check_network_tick()

    def run_forever(self):
        signal.signal(signal.SIGHUP, self.sig_handler)
        signal.signal(signal.SIGQUIT, self.sig_handler)
        signal.signal(signal.SIGINT, self.sig_handler)
        signal.signal(signal.SIGTERM, self.sig_handler)

        signal.signal(signal.SIGALRM, self.alarm_handler)
        signal.setitimer(signal.ITIMER_REAL, 0, ALARM_INTERVAL)

        self.event_loop()

        signal.signal(signal.SIGHUP, None)
        signal.signal(signal.SIGQUIT, None)
        signal.signal(signal.SIGINT, None)
        signal.signal(signal.SIGTERM, None)
        signal.signal(signal.SIGALRM, None)
        signal.setitimer(signal.ITIMER_REAL, 0, 0)

    def run_forever_win32(self):
        signal.signal(signal.SIGINT, self.sig_handler)
        signal.signal(signal.SIGTERM, self.sig_handler)

        self.alarm_handler(None, None)
        while True:
            try:
                self.event_loop(ALARM_INTERVAL)
                break
            except queue.Empty:
                self.alarm_handler(None, None)

        signal.signal(signal.SIGINT, None)
        signal.signal(signal.SIGTERM, None)

    def run(self):
        logger.info(f'Selenium version: {selenium.__version__}')
        logger.info(f'Platform: {sys.platform}')

        self.user = load_user()
        logger.info(f'User: {self.user.username}, {self.user.password}, {self.user.userType}')

        self.check_driver_tick()

        if sys.platform == 'win32':
            logger.warning('Running on Windows is not recommended')
            self.run_forever_win32()
        else:
            self.run_forever()

        logger.info("Exit")


# 测试互联网是否连接
def is_network_connect():
    try:
        status = requests.get(NETWORK_CHECK_URL, timeout=NETWORK_CHECK_TIMEOUT, allow_redirects=False)
        if status.content == NETWORK_CHECK_CONTENT:
            return True
        else:
            return False
    except (requests.ConnectionError,
            requests.HTTPError,
            requests.ConnectTimeout,
            requests.ReadTimeout,
            requests.Timeout):
        return False


def is_ruijie_connect():
    try:
        requests.get(RUIJIE_LOGIN_URL, timeout=NETWORK_CHECK_TIMEOUT, allow_redirects=False)
    except (requests.ConnectionError,
            requests.HTTPError,
            requests.ConnectTimeout,
            requests.ReadTimeout,
            requests.Timeout):
        return False
    return True


def my_chrome_options():
    options = ChromeOptions()
    options.add_argument('--blink-settings=imagesEnabled=false')  # 无图浏览。
    options.add_argument('--no-sandbox')  # 关闭沙箱，可在 root 运行
    options.add_argument('--disable-gpu')  # 禁用 GPU 加速
    options.add_argument('--disable-dev-shm-usage')
    if not DEBUG:
        options.add_argument('--headless')  # 无界面
    options.add_argument('--window-size=1920x1080')  # 设置浏览器分辨率（窗口大小）
    options.accept_insecure_certs = True
    options.timeouts = {"implicit": IMPLICIT_WAIT_TIMEOUT * 1000,
                        "pageLoad": PAGE_LOAD_TIMEOUT * 1000,
                        "script": SCRIPT_TIMEOUT * 1000}
    return options


def load_user() -> User:
    user = User()
    with open(CONF_FILE) as file:
        data = json.load(file)
        user.username = data['username']
        user.password = data['password']
        user.userType = int(data['type'])
    return user


def main():
    log_handlers = [
        MyLogFileHandler(LOG_FILE),
        MyLogStreamHandler()
    ]
    logging.basicConfig(level=logging.NOTSET, handlers=log_handlers)
    logging.captureWarnings(True)

    MyApp().run()


if __name__ == '__main__':
    main()
