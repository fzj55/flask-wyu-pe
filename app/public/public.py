"""中间件"""
import json
import os
from io import BytesIO

from flask import request, Blueprint, g, make_response, redirect, send_file
from werkzeug.security import check_password_hash

from app.model import User, Place, TimeTable, Order, DrawTime
from exts import cache, db
from settings import Config
from utils.http import render_json
from utils.img_VCode import generate_image

from utils.token import token_confirm

public_bp=Blueprint('public', __name__, url_prefix='/')


check_login_route=['order','user','admin','draworder']

@public_bp.before_app_request
def before_request():
    """登录验证"""
    try:
        path = request.path.split('/')[1]
    except:
        return render_json([],1004,'非法尝试')
    if (path in check_login_route) or ('/user/message_port' in request.path):
        token = request.headers.get('token', None) or request.args.get('token', None)
        uid = request.args.get('user_id', None) or request.form.get('user_id', None)

        if not token or not uid:
            return render_json([], 1000, '缺少参数')

        try:
            uid= token_confirm.confirm_validate_token(token, uid)
        except:
            return render_json([], 1001, '用户未登录')
        user = User.get(uid)
        if not user:
            return render_json([],1002,'没有此用户')
        # 验证成功
        g.user=user

@public_bp.route('')
def index():
    return redirect('https://test.wyu-pesystem.com/static/adminUI/templete/login.html')

@public_bp.route('/ImgVcode_port')
def imgVcode_port():
    """图片"""
    ip=request.remote_addr
    # ip = request.headers.get('X-Real-IP', None)
    # if not ip:
    #     return render_json([], 1004, '非法尝试')
    print(ip)
    im, code = generate_image()
    cache.set('ImgVcode:%s' % ip, code, timeout=360)
    print('-' * 20, code)
    buffer = BytesIO()
    im.save(buffer, 'JPEG')
    buf_bytes = buffer.getvalue()
    response = make_response(buf_bytes)
    response.headers['Content-Type'] = 'image/jpg'
    return response

@public_bp.route('/login_port',methods=['POST'])
def login_port():
    ip=request.remote_addr
    print(ip)
    # ip = request.headers.get('X-Real-IP', None)
    # if not ip:
    #     return render_json([], 1004, '非法尝试')

    try:
        data=json.loads(request.data)
    except:
        data=request.form

    name=data.get('name',None)
    password=data.get('password',None)
    code=data.get('code',None)

    print('-'*20,name,password,code)

    if not name or not password or not code:
        return render_json([],1000,'缺少参数')

    right_code=cache.get('ImgVcode:%s' % ip)
    if right_code:
        if right_code.lower()==code.lower():
            user=User.query.filter(User.name==name).first()
            print('-'*20)
            print(user)
            print(password)
            if user and check_password_hash(user.password,password):
                token=token_confirm.generate_validte_token(user.id)
                return render_json({'user_id':user.id,'token':token})
            else:
                return render_json([],1103,'用户名或密码错误')
        else:
            return render_json([],1102,'验证码错误')
    else:
        return render_json([],1101,'图片二维码失效')


@public_bp.route('del')
def dele():
    users = User.query.all()
    for u in users:
        cache.delete('Model:User:%s' % u.id)

    places = Place.query.all()
    for p in places:
        cache.delete('Model:Place:%s' % p.id)

    draw = DrawTime.query.all()
    for d in draw:
        cache.delete('Model:DrawTime:%s' % d.id)

    time=TimeTable.query.all()
    for t in time:
        cache.delete('Model:TimeTable:%s'%t.id)


    order=Order.query.all()
    for o in order:
        cache.delete('Model:Order:%s' % o.id)

    return '1'

@public_bp.route('check_login_port')
def check_login():
    token = request.headers.get('token', None) or request.args.get('token', None)
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

    return render_json([])


@public_bp.route('/get_instruction_port')
def get_instruction_port():
    return send_file(os.path.join(Config.STATIC_DIR, 'word', 'instruction.docx'), as_attachment=True,
                     attachment_filename="小程序使用界面（2022.06.08）.docx")
