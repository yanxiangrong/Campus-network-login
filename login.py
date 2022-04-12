import requests
import selenium.common.exceptions
from func_timeout import func_set_timeout
from selenium import webdriver
import time


# 测试互联网是否连接
def is_connect_web():
    try:
        status = requests.get("http://www.msftconnecttest.com/connecttest.txt")
        if status.content == b"Microsoft Connect Test":
            return True
        else:
            return False
    except requests.exceptions:
        return False

@func_set_timeout(600)
def login():
    options = webdriver.ChromeOptions()
    options.add_argument('blink-settings=imagesEnabled=false')  # 无图浏览。
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.get("http://172.30.30.72/")  # 这个是校园网登录页面的地址。

    try:
        # 找用户名输入框。
        username = driver.find_element_by_id("username")
        # username.clear()
        username.send_keys("xxxxxxxxxx")  # 这个是登录的账号。

        # 这是个安全机制，密码框是隐藏的。要点一下 pwd_tip 密码框才会出来。
        password_tip = driver.find_element_by_id("pwd_tip")
        password_tip.click()

        # 找密码输入框。
        password = driver.find_element_by_id("pwd")
        # password.clear()
        password.send_keys("xxxxxx")  # 这个是登录的密码。

        # 找连接类型选择框。
        select = driver.find_element_by_id("selectDisname")
        select.click()

        # 找学生用户。
        student = driver.find_element_by_id("_service_1")
        student.click()

        # 找登录按钮。
        login_button = driver.find_element_by_id("loginLink_div")
        login_button.click()
    except Exception as err:
        print(err)
    finally:
        driver.close()


# 打印测试信息。
def log(content):
    file = open("log.txt", "a")
    print(content)
    file.write(content + '\n')
    file.close()


def main():
    while True:
        if not is_connect_web():
            print("网络已断开，正在尝试登录校园网...")
            login()
        time.sleep(5)
        #log("test")


if __name__ == '__main__':
    main()


