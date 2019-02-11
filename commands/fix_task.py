# -*- coding: utf-8 -*-
from flask_script import Command


class FixTask(Command):
    """Task to fix data of system """

    def run(self):
        from app.tasks import wpp_refresh_spider

        wpp_refresh_spider.apply_async(args=[])
