# vimage
自动同步微信公众号文章列表

## 系统要求：
- Python 3.6+、Flask 1.0+、virtualenv3.5
- Mysql 5.0+、Redis
- Nginx/1.8.0
- gevent (1.1.2)
- gunicorn (19.6.0)
- celery

## 安装套件管理工具: Homebrew

可以直接点进官网查看安装方式，安装命令：
`/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`

安装完可以跑一下：`brew --version`，如果出现：Homebrew ***证明安装成功了。

## 安装Python3

一种是直接到Python官网下载，另一种是在终端下输入：`brew install python3`


## 安装Redis

`brew install redis`

## 安装selenium

`pip3 install selenium`

## 安装ChromeDriver

下载ChromeDriver, 注意版本需与浏览器版本对应，附：版本号对应描述（64位浏览器下载32位即可），下载后与chrome安装目录放在一起，
然后配置至环境变量即可，配置好后shell输入：chromedriver 无错误即安装成功！


使用**virtualenv**安装创建独立的Python环境

项目运行于 `Python3` 环境下：

    virtualenv py3env --python=python3

启动虚拟环境：

    source py3env/bin/activate

退出虚拟环境：

    deactivate
    
## 测试环境启动

    python3 manage.py server
    
## 开启任务前，先获取cookie信心
    
    python3 manage.py get_wx_cookie
    
## 常用扩展说明

flower - 针对Celery的基于网页的实时管理工具, 启动命令：

    celery flower -A celery_runner --loglevel=info
    
    # 启动work
    celery worker -A celery_runner -f /var/log/mix-wxpider/celery.log -D
    
    # 启动beat
    celery beat -A celery_runner -f /var/log/mix-wxpider/celery.log --detach