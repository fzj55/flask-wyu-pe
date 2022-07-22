import datetime

from flask import Blueprint, request

from app.model import Order
from utils.http import render_json

admin_order_bp=Blueprint('admin_order',__name__,url_prefix='/admin/order')

@admin_order_bp.route('/select_port')
def select_port():
    start_time=request.args.get('start_time')
    end_time=request.args.get('end_time')
    base = request.args.get('base', 'create_time')
    sort_order = request.args.get('sort_order', 'desc')

    orders = Order.query

    if start_time:
        try:
            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        except:
            return render_json([], 2102, '日期格式错误')

        orders.filter(Order.create_time>=start_time)

    if end_time:
        try:
            end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        except:
            return render_json([], 2102, '日期格式错误')

        orders.filter(Order.create_time <= end_time)

    if not (sort_order == 'desc' or sort_order == 'asc'):
        return render_json([], 2405, 'sort_order选值错误')
    sort_base='Order.%s.%s'%(base,sort_order)
    try:
        orders=orders.order_by(eval(sort_base))
    except:
        return render_json([],2404,'base选值错误')

    data=[]
    for order in orders.all():
        orderdetail = order.to_detail_dict()
        orderdetail['user'] = order.user.to_dict()
        data.append(orderdetail)

    return render_json(data)
