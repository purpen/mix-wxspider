# -*- coding: utf-8 -*-
##
# 通过selenium + webdriver获取公众号Cookie
##
import time
import json
from selenium import webdriver
from flask_script import Command

from config import basedir

wpp_account = 'ainela@urknow.com'
wpp_passwd = 'LiBei123'


class WxCookie(Command):
    """
    获取公众号登录的cookie信息
    """

    def run(self):
        print('Begin to get cookie data!')

        post = {}

        driver = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver')
        driver.get('https://mp.weixin.qq.com')

        time.sleep(2)

        driver.find_element_by_name('account').clear()
        driver.find_element_by_name('account').send_keys(wpp_account)
        driver.find_element_by_name('password').clear()
        driver.find_element_by_name('password').send_keys(wpp_passwd)

        # 自动输完密码之后，记得点一下记住我
        time.sleep(5)
        driver.find_element_by_xpath("./*//a[@class='btn_login']").click()

        # 拿手机扫二维码
        time.sleep(30)

        driver.get('https://mp.weixin.qq.com/')
        cookie_items = driver.get_cookies()
        for cookie_item in cookie_items:
            post[cookie_item['name']] = cookie_item['value']

        cookie_str = json.dumps(post)
        cookie_file = '%s/cookie.txt' % basedir
        with open(cookie_file, 'w+', encoding='utf-8') as f:
            f.write(cookie_str)

        print('End get cookie data!')
