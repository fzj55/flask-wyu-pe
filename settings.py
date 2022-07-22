import os

from apscheduler.jobstores.redis import RedisJobStore


class Config:
    DEBUG = True
    SECRET_KEY='yfyuvkbu2651561#%#$sKJBJB156'
    # 项目路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # 静态文件夹的路径
    STATIC_DIR = os.path.join(BASE_DIR, 'static')
    # 头像的上传目录
    UPLOAD_ICON_DIR = os.path.join(STATIC_DIR, 'upload/icon')

    SQLALCHEMY_DATABASE_URI='mysql+pymysql://root:433213820gt@$@localhost:3306/yuyue2_1'#'sqlite:///db.sqlite3'
    CSQLALCHEMY_TRACK_MODIFIATIONS=False
    SQLALCHEMY_ECHO=True

    #动态定时任务
    SCHEDULER_API_ENABLED = True
    SCHEDULER_JOBSTORES = {
        'default': RedisJobStore(db=2, host='127.0.0.1', port='6379')
    }
    SCHEDULER_EXECUTORS = {
        'default': {'type': 'threadpool', 'max_workers': 10}
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_COMMIT_TEARDOWN = True
    SCHEDULER_TIMEZONE='Asia/Shanghai'


class DevelopmentConfig(Config):
    ENV='development'

class ProductionConfig(Config):
    ENV='production'
    DEBUG = False
