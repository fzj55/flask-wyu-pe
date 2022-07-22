from flask_apscheduler import APScheduler
from flask_caching import Cache
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy


db=SQLAlchemy()
cache=Cache()
cors=CORS()
scheduler = APScheduler()
