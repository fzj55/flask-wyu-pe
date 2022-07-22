from flask import Blueprint, request

from app.model import Notice
from utils.http import render_json

notice_bp=Blueprint('notice',__name__,url_prefix='/notice')

@notice_bp.route('/urgent_port')
def urgent_port():
    """紧急公告"""
    notice=Notice.query.filter(Notice.is_urgent==True).order_by(Notice.create_time.desc()).first()
    if notice:
        return render_json(notice.to_dict())
    else:
        return render_json([])

@notice_bp.route('/normal_port')
def normal_port():
    """公告详情"""
    datalist=[]
    place_id=request.args.get('id',None)
    if place_id:
        notices=Notice.query.filter(Notice.place_id==place_id).order_by(Notice.create_time.desc()).limit(3).all()
        if notices:
            for notice in notices:
                datalist.append(notice.to_dict(date_time=1))
            return render_json(datalist)
        else:
            return render_json([],1201,'此场所没有发布公告')
    else:
        return render_json([],1000,'缺少参数')