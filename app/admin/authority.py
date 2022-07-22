from flask import Blueprint, request, g

from utils.http import render_json

admin_authority_bp=Blueprint('admin_authority',__name__,url_prefix='/admin/authority')

need_authority = ['1']

@admin_authority_bp.before_app_request
def before_request():
    try:
        path = request.path.split('/')[1]
    except:
        return render_json([], 1005, '路径错误')
    if path == 'admin':
        if not g.user.authority_id in need_authority:
            return render_json([], 1003, '没有权限')
