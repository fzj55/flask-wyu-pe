import datetime
import json
import os
import uuid

from flask import Blueprint, request, send_file
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import openpyxl as vb

from app.admin.logic import add_user
from app.model import User, Authority
from exts import db
from settings import Config
from utils.http import render_json

admin_user_bp = Blueprint('admin_useer', __name__, url_prefix='/admin/user')


@admin_user_bp.route('/insert_port', methods=['POST'])
def insert_port():
    try:
        data = json.loads(request.data)
    except:
        data = request.form

    name = data.get('name')
    password = data.get('password')
    img = data.get('img')
    reset_time = data.get('reset_time')
    authority_id = data.get('authority_id')
    data=add_user(name,password,img,reset_time,authority_id)
    return render_json(data[0],data[1],data[2])


@admin_user_bp.route('/select_port')
def select_port():
    base = request.args.get('base')
    sort_order = request.args.get('sort_order', 'desc')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))

    users = User.query
    if base:
        if sort_order != 'asc' or sort_order != 'desc':
            return render_json([], 2405, 'sort_order选值错误')
        sort_base = 'User.%s.%s()' % (base, sort_order)
        try:
            users = users.order_by(eval(sort_base))
        except:
            return render_json([], 2404, 'base选值错误')

    data = []
    for user in users.paginate(page=page, per_page=page_size).items:
        data.append(user.to_dict(0, False, 'password'))

    return render_json(data)


@admin_user_bp.route('/update_port', methods=['POST'])
def update_port():
    try:
        data = json.loads(request.data)
    except:
        data = request.form

    id = data.get('id')
    name = data.get('name')
    password = data.get('password')
    img = data.get('img')
    reset_time = data.get('reset_time')
    authority_id = data.get('authority_id')

    if not (id and name and authority_id):
        return render_json([], 1000, '缺少参数')

    user = User.query.get(id)
    if not user:
        return render_json([], 1002, '没有此用户')

    another_user = User.query.filter(User.id != user.id, User.name == name).first()
    if another_user:
        return render_json([], 2302, '用户已经存在')

    if reset_time:
        try:
            reset_time = datetime.datetime.strptime(reset_time, '%Y-%m-%d %H:%M:%S')
        except:
            return render_json([], 2102, '日期格式错误')

    authority = Authority.get(authority_id)
    if not authority:
        return render_json([], 2301, '此权限没在数据库中')
    if authority.id != '-1' and reset_time:
        return render_json([], 2303, '此用户不在黑名单无需设置重置时间')
    if authority.id == '-1' and not reset_time:
        return render_json([], 2304, '此用户在黑名单中请设置重置时间')

    user.name = name
    if password:
        user.password = generate_password_hash(password)
    user.img = img
    user.reset_time = reset_time
    user.authority_id = authority.id
    db.session.add(user)
    try:
        db.session.commit()
    except:
        return render_json([], 1006, '数据库错误')
    return render_json([])


@admin_user_bp.route('delete_port')
def delete_port():
    id = request.args.get('id')
    user = User.query.get(id)
    if not user:
        return render_json([], 1002, '没有此用户')
    try:
        user.delete()
    except:
        return render_json([], 1006, '数据库错误')

    return render_json([])


@admin_user_bp.route('get_template_port')
def get_template_port():
    return send_file(os.path.join(Config.STATIC_DIR, 'excel', 'template.xlsx'), as_attachment=True,
                     mimetype='application/vnd.ms-excel')

@admin_user_bp.route('batch_add_port',methods=['POST'])
def batch_add_port():
    template=request.files.get('template')
    template_name = template.filename
    suffix = template_name.rsplit('.')[-1]
    if suffix in 'xlsx':
        template_name = secure_filename(template_name)
        if template_name.rsplit('.')[0]=='template':
            template_name=template_name.rsplit('.')[0]+'new.xlsx'
        file_path= os.path.join(Config.STATIC_DIR, 'excel', template_name)
        template.save(file_path)
        excel_file=vb.load_workbook(file_path)
        table = excel_file.worksheets[0]
        n=0
        for row,value in enumerate(table.values):
            if n==0:
                n+=1
                continue
            data=add_user(str(value[0]),str(value[1]),None,value[2],str(value[3]))
            if data[1] != 0:
                error='第%s行用户信息错误(之前的用户已经录入好请删除再录入)：'%str(row+1)+data[2]
                os.remove(file_path)
                return render_json([],2306,error)
        os.remove(file_path)
        return render_json([])
    else:
        return render_json([],2305,'文件类型错误')