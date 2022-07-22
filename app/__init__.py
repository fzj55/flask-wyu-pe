import atexit
import platform

from flask import Flask
from flask_apscheduler import APScheduler

import settings
from app.admin.authority import admin_authority_bp
from app.admin.notice import admin_notice_bp
from app.admin.order import admin_order_bp
from app.admin.timetable import admin_timetable_bp
from app.admin.user import admin_user_bp
from app.normal_user.authority import authority_bp
# from app.normal_user.draw import draw_bp
from app.admin.drawtime import admin_drawtime_bp
# from app.normal_user.draworder import draworder_bp
from app.normal_user.drawtime import drawtime_bp

from app.normal_user.notice import notice_bp
from app.normal_user.order import order_bp
from app.normal_user.place import place_bp
from app.private.authority import private_authority_bp
from app.private.order import private_order_bp
from app.private.drawtime import private_drawtime_bp
from app.private.user import private_user_bp
from app.public.public import public_bp
from app.normal_user.user import user_bp

from exts import db, cache, cors, scheduler

#rides缓存配置
config={
    'CACHE_TYPE':'redis',
    'CACHE_REDIS_HOST':'127.0.0.1',
    'CACHE_REDIS_PORT':6379,
}

def create_app():
    app=Flask(__name__,template_folder='../templates',static_folder='../static')
    app.config.from_object(settings.DevelopmentConfig)
    db.init_app(app=app)
    cache.init_app(app=app,config=config)
    cors.init_app(app=app, support_credentials=True)
    scheduler.init_app(app)
    scheduler.start()

    app.register_blueprint(public_bp)
    app.register_blueprint(authority_bp)
    app.register_blueprint(notice_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(place_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(user_bp)
    # app.register_blueprint(draworder_bp)
    app.register_blueprint(drawtime_bp)
    app.register_blueprint(admin_authority_bp)
    app.register_blueprint(admin_timetable_bp)
    app.register_blueprint(admin_notice_bp)
    app.register_blueprint(admin_user_bp)
    app.register_blueprint(admin_drawtime_bp)
    app.register_blueprint(admin_order_bp)
    app.register_blueprint(private_authority_bp)
    app.register_blueprint(private_drawtime_bp)
    app.register_blueprint(private_user_bp)
    app.register_blueprint(private_order_bp)

    return app