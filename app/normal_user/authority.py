from flask import Blueprint, request, g

from utils.http import render_json

authority_bp=Blueprint('authority',__name__,url_prefix='/authority')

check_authority = ['order','draworder']
need_authority = ['0','1']

@authority_bp.before_app_request
def before_request():
    try:
        path = request.path.split('/')[1]
        print('-'*20,path)
    except:
        return render_json([], 1005, '路径错误')
    if path in check_authority:
        if not g.user.authority_id in need_authority:
            if g.user.authority_id=='-1':
                return render_json([], 1003, '您被加入了黑名单')
            return render_json([], 1003, '没有权限')