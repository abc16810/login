# coding: utf-8

from http import cookiejar
from PIL import Image
import matplotlib.pyplot as plt
import requests
import time
import re
import json
import base64
import hmac
import hashlib


HEADERS = {
   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
   "Accept-Encoding": "gzip, deflate, br",
   "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
   "Connection": "keep-alive",
   "Host": "www.zhihu.com",
   "Upgrade-Insecure-Requests": "1",
   "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0",
}

LOGIN_URL = 'https://www.zhihu.com/signup'
LOGIN_API = 'https://www.zhihu.com/api/v3/oauth/sign_in'

FORM_DATA = {

  "client_id": "c3cef7c66a1843f8b3a9e6a1e3160e20",
  "grant_type": "password",
  "source": "com.zhihu.web",
  "username": '',
  "password": '',
  "lang": "cn",
  "ref_source": "homepage",
}


class ZHIHULogin(object):
 
    def __init__(self):

        self.login_url = LOGIN_URL
        self.login_api = LOGIN_API
        self.login_data = FORM_DATA
        self.session = requests.session()
        self.headers = HEADERS.copy()
        self.cookies = cookiejar.LWPCookieJar(filename='./cookies.txt')
        

    def login(self, load_cookies=True):
        
        """
        模拟登录知乎
        :param load_cookies: 是否读取上次保存的 Cookies
        :return: bool
        """
        if load_cookies and self.load_cookies():
            if self.check_login():
                print('已读取 Cookies 并登录成功')
                return True
            else:
                print('保存的 Cookies 已过期，将重新登录')


        headers = self.headers.copy()
        xsrf, udid = self._get_token_udid()
        print(self.session.cookies.get_dict())
        headers.update({
           "x-udid": udid,
           "x-xsrftoken": xsrf,
           'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
         })
        headers.update({'origin': 'https://www.zhihu.com','Referer': 'https://www.zhihu.com/signup','Accept': 'application/json, text/plain, */*'})
        self.login_data.update({
            'username': self._input_data('username', '登录手机'),
            'password': self._input_data('password', '密码')
        })
        timestamp = str(int(time.time()*1000))
        self.login_data.update({
            "timestamp": timestamp,
            "signature": self._get_signature(timestamp),
            "captcha": self._get_captcha(headers.copy()),
          })

        res = self.session.post(self.login_api, data=self.login_data, headers=headers)
        print(self.session.cookies.get_dict())
        print(res.text,res.status_code)
        if '验证码' in res.text:
            print('验证码错误')
        elif self.check_login():
            print('登录成功')
            return True
        print('登录失败')
        return False


    def load_cookies(self):
        
        """
        读取 Cookies 文件加载到 Session
        :retur
        """
        try:
            self.cookies.load(ignore_discard=True)
        except FileNotFoundError:
            print('Cookies.txt 未找到，读取失败')
        else:
            #工具方法转换成字典
            load_cookies = requests.utils.dict_from_cookiejar(self.cookies)
            #工具方法将字典转换成RequestsCookieJar，赋值给session的cookies.
            self.session.cookies = requests.utils.cookiejar_from_dict(load_cookies)
            return True
        return False         

    def check_login(self):
        """
        检查登录状态，访问登录页面出现跳转则是已登录，
        如登录成功保存当前 Cookies
        :return: bool
        """
        res = self.session.get(self.login_url, headers=self.headers, allow_redirects=False)
        print(res.status_code)
        if res.status_code == 302:
            # self.session.cookies.save()
            #将转换成字典格式的RequestsCookieJar（这里我用字典推导手动转的）保存到LWPcookiejar中
            requests.utils.cookiejar_from_dict({c.name: c.value for c in self.session.cookies}, self.cookies)
            self.cookies.save(ignore_discard=True, ignore_expires=True)
            return True
        return False

    def _get_token_udid(self):
        """
        从登录页面获取 token
        :return:
        """
        cookies_dict = {}
        token = udid = None
        res = self.session.get(self.login_url,headers=self.headers) 
        print("请求第一步:状态吗为： %s" % res.status_code)
        if res.status_code == 200:
            # cookies_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
            cookies_dict = self.session.cookies.get_dict()

            if cookies_dict['_xsrf']:
                token = cookies_dict.get('_xsrf')
            if cookies_dict['d_c0']:
                udid = cookies_dict.get('d_c0').split("|")[0].replace("\"","")
        print("token is % and udis is %s" % (token,udid))
        return token, udid


    def _get_captcha(self, headers, lang='cn'):
        """
        请求验证码的 API 接口，无论是否需要验证码都需要请求一次
        如果需要验证码会返回图片的 base64 编码
        可选择两种验证码，需要人工输入
        :param headers: 带授权信息的请求头部
        :param lang: 验证码的种类，中文是选倒立汉字，英文是输入字符
        :return: 验证码的 POST 参数
        """

        if lang == 'cn':
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=cn'
        else:
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'

        if headers.get('x-xsrftoken'):
            headers.pop('x-xsrftoken')
        res = self.session.get(api, headers=headers)
        print("请求第二步:状态吗为: %s" % res.status_code)
        show_captcha = re.search(r'true', res.text)
        if show_captcha:
            put_res = self.session.put(api, headers=headers)
            content = base64.b64decode(josn.loads(put_res)['img_base64'])
            with open('./captcha.png', 'wb') as f:
                f.write(content)
            image = Image.open('./captcha.png')
            if lang == 'cn':
                plt.imshow(img) 
                print('点击所有倒立的汉字，按回车提交')
                points = plt.ginput(7)
                capt = json.dumps({'img_size': [200, 44],'input_points': [[i[0]/2, i[1]/2] for i in points]})
            else:
                img.show()
                capt = input('请输入图片里的验证码：')
           
            # 这里必须先把参数 POST 验证码接口
            self.session.post(api, data={'input_text': capt}, headers=headers)
            return capt
        else:
            print("验证码False")
        return ''


    def _get_signature(self, timestamp):
        """
        通过 Hmac 算法计算返回签名
        实际是几个固定字符串加时间戳
        :param timestamp: 时间戳
        :return: 签名
        https://static.zhihu.com/heifetz/main.app.268c34bc2abd4304ea97.js
        """
        ha = hmac.new(b'd1b964811afb40118a12068ff74a12f4', digestmod=hashlib.sha1)
        grant_type = self.login_data['grant_type']
        client_id = self.login_data['client_id']
        source = self.login_data['source']
        # 顺序不能错
        ha.update(bytes((grant_type + client_id + source + timestamp), 'utf-8'))
        signature = ha.hexdigest()
        print('签名字符串为:%s' % signature)
        return signature

    def _input_data(self, key, data_name):
        """
        用于手动输入指定 form_data 参数
        :param key: 键名
        :param data_name: 用于输入提示中文名
        :return: 输入的值
        """
        value = self.login_data.get(key)
        if not value:
            value = input('请输入{}：'.format(data_name))
        return value


if __name__ == '__main__':
    account = ZHIHULogin()
    account.login()
    # 登陆成功后请求如下页面测试
    # headers 里保留到如下即可正常 否则出现乱码
    # h: {'Host': 'zhuanlan.zhihu.com', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0', 'Referer': 'https://www.zhihu.com/'}
    # res = s.get('https://zhuanlan.zhihu.com/p/35986817',headers=h)
