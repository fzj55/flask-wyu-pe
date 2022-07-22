from flask import Blueprint, request

from utils.http import render_json

private_authority_bp=Blueprint('private_authority', __name__, url_prefix='/private/authority')

@private_authority_bp.before_app_request
def before_request():
    try:
        path = request.path.split('/')[1]
    except:
        return render_json([], 1005, '路径错误')
    if path == 'private':
        ip = request.headers.get('X-Real-IP', None)
        if not ip:
            ip=request.remote_addr
        if not ip:
            return render_json([], 1004, '非法尝试')
        if ip != '127.0.0.1':
            return render_json([], 1003, '没有权限')