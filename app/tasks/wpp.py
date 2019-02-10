# -*- coding: utf-8 -*-
import re
import json
import requests
from flask import current_app
from app.extensions import fsk_celery
from app.helpers.utils import *

FAIL = 'FAIL'
SKIP = 'SKIP'
SUCCESS = 'SUCCESS'

# 消息头指定
headers = {'Content-Type': 'application/json;charset=UTF-8'}


@fsk_celery.task(name='wpp.refresh_spider')
def wpp_refresh_spider():
    """4小时刷新一次，获取公众号文章增量"""
    last_at = timestamp() - 4*60*60

    # 获取超出12小时的公众号
    payload = {
        'last_at': last_at
    }
    url = '%s/v1.0/wpp/sync_wpp_list' % current_app.config['LX_API_HOST']
    result = requests.post(url, json=payload, headers=headers)
    result = Dictate(result.json())
    if result.status.code and result.status.code != 200:
        current_app.logger.warn('Wpp refresh code: %d' % result.get('errcode'))
        return FAIL

    current_app.logger.debug(result)

    for wpp in result.data.wpps:
        wpp_spider_articles.apply_async(args=[wpp['master_uid'], wpp['id'], wpp['alias'], wpp['last_spider_at']])

    return SUCCESS


@fsk_celery.task(name='wpp.sync_latest')
def wpp_sync_latest():
    """自动同步最新公众号文章"""
    last_at = timestamp() - 60  # 自动同步最近1分钟内的公众号

    payload = {
        'last_at': last_at
    }
    url = '%s/v1.0/wpp/sync_wpp_latest' % current_app.config['LX_API_HOST']
    result = requests.post(url, json=payload, headers=headers)

    result = Dictate(result.json())

    if result.status.code and result.status.code != 200:
        current_app.logger.warn('Wpp sync error message: %s' % result.status.message)
        return FAIL

    current_app.logger.debug(result)

    for wpp in result.data.wpps:
        wpp_spider_articles.apply_async(args=[wpp['master_uid'], wpp['id'], wpp['alias'], wpp['last_spider_at']])

    return SUCCESS


@fsk_celery.task(name='wpp.spider_all_articles')
def wpp_spider_articles(master_uid, wpp_id, wpp_name, last_spider_at=0):
    """通过公众号名称或微信号，爬取公众号全部文章列表"""
    if not wpp_name:
        current_app.logger.warn('Wpp name is empty!')
        return FAIL

    url = 'https://mp.weixin.qq.com'
    header = {
        'HOST': 'mp.weixin.qq.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
    }

    cookie_file = '%s/cookie.txt' % current_app.config['WPP_COOKIE_PATH']
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookie = f.read()

    if not cookie:
        current_app.logger.warn("Wpp spider cookie isn't exist!")
        return FAIL

    cookies = json.loads(cookie)
    response = requests.get(url=url, cookies=cookies)

    current_app.logger.warn("Wpp spider token res[%s]!" % response.url)

    token = re.findall(r'token=(\d+)', str(response.url))[0]

    current_app.logger.warn('Wpp spider token: %s' % token)

    # 查找匹配的公众号
    query_id = {
        'action': 'search_biz',
        'token': token,
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
        'random': random.random(),
        'query': wpp_name,
        'begin': '0',
        'count': '5',
    }
    search_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?'

    search_response = requests.get(search_url, cookies=cookies, headers=header, params=query_id)
    tmp_url = search_response.url

    current_app.logger.warn('Wpp spider url: %s' % tmp_url)

    lists = search_response.json().get('list')[0]

    current_app.logger.warn('Wpp spider list: %s' % lists)

    # 获取公众号的文章列表
    fakeid = lists.get('fakeid')
    per_page = 5
    page = 1
    is_loop = True
    while is_loop:
        start = (page - 1) * per_page
        query_id_data = {
            'token': token,
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1',
            'random': random.random(),
            'action': 'list_ex',
            'begin': str(start),
            'count': str(per_page),
            'query': '',
            'fakeid': fakeid,
            'type': '9'
        }

        current_app.logger.debug('Wpp params: %s' % query_id_data)

        appmsg_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?'
        appmsg_response = requests.get(appmsg_url, cookies=cookies, headers=header, params=query_id_data)
        tmp_url2 = appmsg_response.url

        current_app.logger.warn('Wpp spider list url: %s' % tmp_url2)

        max_num = appmsg_response.json().get('app_msg_cnt')  # 发布的文章总数
        article_lists = appmsg_response.json().get('app_msg_list')  # 发布的文章列表

        current_app.logger.warn('Wpp article total count: [%d]----!' % max_num)

        if len(article_lists) == 0:
            current_app.logger.warn('Spider article is empty!!!')
            break

        # 批量导入
        for article in article_lists:
            current_app.logger.debug('article: %s' % article)

            # 更新时间小于上次抓取时间
            if article['update_time'] < last_spider_at:
                current_app.logger.warn('last spider: %s, article: %s' % (last_spider_at, article['update_time']))
                is_loop = False
                break

            # 导入数据库
            wpp_add_article.apply_async(args=[master_uid, article])

        # 循环下一页
        page += 1

        # 延迟15s
        time.sleep(15)

    last_update_at = timestamp()
    current_app.logger.warn('Wpp spider list is ok, updated time[%s]!' %
                            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    # 更新公众号最后抓取时间
    payload = {
        'last_at': last_update_at,
        'wpp_id': wpp_id
    }
    url = '%s/v1.0/wpp/update_wpp_last' % current_app.config['LX_API_HOST']
    result = requests.post(url, json=payload, headers=headers)
    result = Dictate(result.json())
    if result.status.code and result.status.code != 200:
        current_app.logger.warn('Wpp spider code: %d' % result.get('errcode'))
        return FAIL

    current_app.logger.warn('Wpp last spider time [%s]!' % last_update_at)

    return SUCCESS


@fsk_celery.task(name='wpp.add_article')
def wpp_add_article(master_uid, article_data):
    """导入公众号文章"""
    try:
        payload = {
            'master_uid': master_uid,
            'article': article_data
        }
        url = '%s/v1.0/wpp/sync_wpp_article' % current_app.config['LX_API_HOST']
        result = requests.post(url, json=payload, headers=headers)
        result = Dictate(result.json())
        if result.status.code and result.status.code != 200:
            current_app.logger.warn('Wpp add code: %d' % result.get('errcode'))
            return FAIL

    except Exception as err:
        current_app.logger.error('Add article fail: {}'.format(str(err)))
        return FAIL

    return SUCCESS
