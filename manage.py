from flask import request
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from app import create_app

from exts import db
from utils.orm import patch_model

app=create_app()
manager=Manager(app=app)
migrate=Migrate(app=app,db=db)
manager.add_command('db',MigrateCommand)
patch_model()

if __name__ == '__main__':
    manager.run()
