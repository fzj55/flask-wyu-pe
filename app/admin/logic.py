import datetime
import uuid

from werkzeug.security import generate_password_hash

from app.model import User, Authority
from exts import db


def add_user(name,password,img,reset_time,authority_id):
    if not (name and password and authority_id):
        return [], 1000, '缺少参数'

    user = User.query.filter(User.name == name).first()
    if user:
        return [], 2302, '用户已经存在'

    if reset_time:
        try:
            reset_time = datetime.datetime.strptime(reset_time, '%Y-%m-%d %H:%M:%S')
        except:
            return [], 2102, '日期格式错误'

    authority = Authority.get(authority_id)
    if not authority:
        return [], 2301, '此权限没在数据库中'
    if authority.id != '-1' and reset_time:
        return [], 2303, '此用户不在黑名单无需设置重置时间'
    if authority.id == '-1' and not reset_time:
        return [], 2304, '此用户在黑名单中请设置重置时间'

    user = User()
    user.id = str(uuid.uuid4())
    user.name = name
    user.password = generate_password_hash(password)
    user.img = img
    user.reset_time = reset_time
    user.authority_id = authority.id
    db.session.add(user)
    try:
        db.session.commit()
    except:
        return [], 1006, '数据库错误'
    return [],0,'成功'
