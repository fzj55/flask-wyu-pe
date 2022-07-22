#消息代理
from datetime import timedelta

from celery.schedules import crontab

BROKER_URL = 'redis://127.0.0.1:6379/1'
#存储任务执行结果
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/1'
#任务的序列化方式
CELERY_TASK_SERIALIZER = 'json'
#任务执行结果的序列化方式
CELERY_RESULT_SERIALIZER = 'json'
#任务过期时间
CELERY_TASK_RESULT_EXPIRES = 60 * 60 * 24
#接受内容类型
CELERY_ACCEPT_CONTENT = ['json']
#超时再分配时间
BROKER_TRANSPORT_OPTIONS ={'visibility_timeout': 3600}
#每个worker执行了多少任务就会死掉，避免内存泄露
CELERYD_MAX_TASKS_PER_CHILD = 500
#时区设置，用于定时任务
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ENABLE_UTC = False
#任务导入，包括异步任务和定时任务
CELERY_IMPORTS = ('celery_task.tasks')
# 计划任务
CELERYBEAT_SCHEDULE ={
    'test_reminders1': {
        #task就是需要执行计划任务的函数
        'task': 'celery_task.tasks.day_update',
        #配置计划任务的执行时间，这里是每60秒执行一次
        'schedule': crontab(minute="05",hour="00"),
        #传入给计划任务函数的参数
        'args': None
    },
    'test_reminders2': {
        #task就是需要执行计划任务的函数
        'task': 'celery_task.tasks.week_update',
        #配置计划任务的执行时间，这里是每60秒执行一次
        'schedule': crontab(minute="06",hour="00",day_of_week=[1]),
        #传入给计划任务函数的参数
        'args': None
    },
}