import datetime
import json
import uuid

from flask import Blueprint, request
from werkzeug.security import generate_password_hash

from app.model import User
from exts import db
from settings import Config

private_user_bp=Blueprint('private_user', __name__, url_prefix='/private/user')

@private_user_bp.route('/add',methods=['POST'])
def add():
    try:
        data=json.loads(request.data)
    except:
        data=request.form
    name=data.get('name')
    password=data.get('password')
    # print('-'*20,name,password)
    user=User()
    user.id=str(uuid.uuid4())
    user.name=name
    user.password=generate_password_hash(password)
    user.authority_id='0'
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        print(e)
        print(name)
        exit()
    return '1'

@private_user_bp.route('/check')
def check():
    fp=open(Config.BASE_DIR+'\\app\\private\\check.txt',encoding='utf-8')
    data=fp.readlines()
    data=list(map(lambda x:x.split('\n')[0],data))
    users=User.query.all()
    print('-'*20)
    for user in users:
        if user.name not in data:
            print(user.name)

    print('='*20)
    names=list(map(lambda x: x.name, users))
    for i in data:
        if i not in names:
            print(i)

    return '1'

@private_user_bp.route('/reset')
def reset():
    users=User.query.filter(User.authority_id=='-1').all()
    for user in users:
        if user.reset_time<datetime.datetime.now():
            user.authority_id=0
            db.session.add(user)
    db.session.commit()
    return '1'

# @private_user_bp.route('/delete')
# def delete():
#     name=request.args.get('name')
#     user=User.query.filter(User.name==name).first()
#     if user:
#         user.delete()
#     return '1'