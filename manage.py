#!venv/bin/python
# -*- coding: utf-8 -*-
import os
from flask_script import Server, Manager, Shell
from flask_script.commands import ShowUrls, Clean
from app import create_app, db
from commands import WxCookie

## 加载环境变量

if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

basedir = os.path.abspath(os.path.dirname(__file__))

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)


@manager.command
def test():
    """Run the unit test."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


def make_shell_context():
    return dict(app=app, db=db)


## 常用操作命令

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('show-urls', ShowUrls())

# 清除工作目录中Python编译的.pyc和.pyo文件
manager.add_command('clean', Clean())

## 初始化系统命令

# 获取公众号登录cookie
manager.add_command('get_wx_cookie', WxCookie())

## 启动测试服务器

server = Server(host='0.0.0.0', port=8080, use_debugger=True)
manager.add_command('server', server)

if __name__ == '__main__':
    manager.run()
