# coding: utf-8

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from io import BytesIO
import time

# 参考
# https://juejin.im/post/5acf0ffcf265da23826e5e20


class CrackWeibo(object):

    def __init__(self):
        self.url = 'https://passport.weibo.cn/signin/login'
        # options = Options()
        # options.add_argument('-headless')  # 无头参数
        # 使用第三方firfox浏览器驱动
        # self.browser = webdriver.Firefox(executable_path='geckodriver', firefox_options=options)
        self.browser = webdriver.Firefox()
        self.wait = WebDriverWait(self.browser, 20)
        self.username = 'USERNAME'
        self.password = 'PASSWORD'

    def __del__(self):
        self.browser.close()


    def open_url(self):
        """
        打开网页输入用户名密码并点击
        :return: None
        """
        self.browser.get(self.url)
        # presence_of_element_located: 元素加载出
        # element_to_be_clickable: 元素可点击
        username = self.wait.until(EC.presence_of_element_located((By.ID, 'loginName')))
        password = self.wait.until(EC.presence_of_element_located((By.ID, 'loginPassword')))
        submit = self.wait.until(EC.element_to_be_clickable((By.ID, 'loginAction')))
        username.send_keys(self.username)
        password.send_keys(self.password)
        submit.click()

    
    def get_position(self):
        """
        获取验证码位置
        :return: 验证码位置元组
        """
        try:
            img = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'patt-shadow')))
        except TimeoutException:
            print('未出现验证码')
            return (None,None,None,None)
        else:
            time.sleep(2)
            location = img.location
            size = img.size
            top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size['width']
            return (top, bottom, left, right)


    def get_screenshot(self):
        """
        获取网页截图
        :return: 截图对象
        """
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot


    def get_image(self, name='captcha.png'):
        """
        获取验证码图片
        :return: 图片对象
        """
        top, bottom, left, right = self.get_position()
        if not (top and  bottom and left and right):
            return None
        else:
            print('验证码位置', top, bottom, left, right)
            screenshot = self.get_screenshot()
            captcha = screenshot.crop((left, top, right, bottom))
            captcha.save(name)
            return captcha

    
    def main(self):
        """
        批量获取验证码
        :return: 图片对象
        """
        count = 0
        while count<10:
            self.open_url()
            self.get_image(str(count) + '.png')
            count += 1

if __name__ == '__main__':
    crack = CrackWeibo()
    crack.main()
