import datetime
import json
import uuid

from flask import Blueprint, request, g
from werkzeug.security import check_password_hash

from app.model import User, TimeTable, Order, Place, DrawTime
from exts import cache
from utils.http import render_json
from utils.start_end_time import get_week_start_end_time
from utils.token import token_confirm

user_bp=Blueprint('user',__name__,url_prefix='/user')


@user_bp.route('/logout_port')
def logout_port():
    token = request.headers.get('token', None) or request.query_params.get('token', None)
    uid = request.args.get('user_id', None) or request.form.get('user_id', None)

    if not token or not uid:
        return render_json([], 1000, '缺少参数')

    try:
        uid = token_confirm.confirm_validate_token(token, uid)
    except:
        return render_json([], 1001, '用户未登录')
    user = User.get(uid)
    if not user:
        return render_json([], 1002, '没有此用户')

    token_confirm.remove_validate_token(token,uid)
    return render_json([])

@user_bp.route('/message_port')
def message_port():
    return render_json(g.user.to_dict(0,False,'password'))

@user_bp.route('/residue_degree_port')
#检验剩余次数
def residue_degree():
    data=[]
    places=Place.query.filter(Place.parent_id=='-1').all()
    for place in places:
        residue_num=g.user.get_residue_degree(place.id)
        data.append({'name':place.name,'times':residue_num})
    return render_json(data)

@user_bp.route('/auth_code')
def auth_code():
    if cache.get('authcode_time:%s'%g.user.id):
        return render_json([],1104,'未到30秒无法刷新')
    auth=str(uuid.uuid4())
    cache.set('authcode:%s'%auth,g.user,360)
    cache.set('authcode_time:%s'%g.user.id,'1',30)
    return render_json(auth)

