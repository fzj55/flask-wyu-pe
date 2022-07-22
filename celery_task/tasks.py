import datetime

import requests

from celery_task.celery import celery_app
from log import logger


@celery_app.task(name='celery_task.tasks.day_update')
def day_update():
    resp = requests.request(method='get', url='http://127.0.0.1:5000/private/drawtime/cycle_time')
    if resp.status_code != 200:
        logger.error('循环时间设置失败')
        return 0

    resp = requests.request(method='get', url='http://127.0.0.1:5000/private/user/reset')
    if resp.status_code != 200:
        logger.error('用户重置失败')
        return 0

    resp = requests.request(method='get', url='http://127.0.0.1:5000/private/order/delete_drawfail')
    if resp.status_code != 200:
        logger.error('失败未中签')
        return 0

    return 1

@celery_app.task(name='celery_task.tasks.week_update')
def week_update():
    resp = requests.request(method='get', url='http://127.0.0.1:5000/private/timetable/remove_timeout')
    if resp.status_code != 200:
        logger.error('时间删除失败')
        return 0