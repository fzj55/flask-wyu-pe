import datetime
import json
import uuid

from flask import Blueprint, request

from app.model import Notice
from exts import db
from utils.http import render_json

admin_notice_bp=Blueprint('admin_notice',__name__,url_prefix='/admin/notice')

@admin_notice_bp.route('/announce_port',methods=['POST'])
def announce_port():
    try:
        data=json.loads(request.data)
    except:
        data=request.form
    place_id=data.get('place_id',None)
    content=data.get('content',None)
    is_urgent=data.get('is_urgent',0)
    title=data.get('title',None)

    try:
        is_urgent=int(is_urgent)
    except:
        is_urgent=0

    if place_id and content and title:
        notice=Notice()
        notice.id=str(uuid.uuid4())
        notice.title=title
        notice.content=content
        notice.is_urgent=is_urgent
        notice.create_time=datetime.datetime.now()
        notice.place_id=place_id
        try:
            db.session.add(notice)
            db.session.commit()
        except Exception as e:
            print(e)
            return render_json([],1006,'数据库错误')
        return render_json([])
    else:
        return render_json([],1000,'缺少参数')


@admin_notice_bp.route('/del_port', methods=['GET'])
def del_port():
    notice_id = request.args.get('notice_id', None)
    if not notice_id:
        return render_json([], 1000, '缺少参数')
    notice = Notice.query.get(notice_id)
    if not notice:
        return render_json([], 2412, '查无此公告')

    try:
        db.session.delete(notice)
        db.session.commit()
    except:
        return render_json([], 1006, '数据库错误')
    return render_json([])

@admin_notice_bp.route('/search_port', methods=['GET'])
def search_port():
    place_id =request.args.get('place_id', None)
    if not place_id:
        return render_json([], 1000, '缺少参数')

    notices = Notice.query.filter(Notice.place_id == place_id).all()
    datalist = []
    if not notices:
        return render_json([], 1201, '此场所没有发布公告')

    for notice in notices:
        datalist.append(notice.to_dict())
    return render_json(datalist)
