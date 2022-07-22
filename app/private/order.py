from flask import Blueprint

from app.model import Order

private_order_bp=Blueprint('private_order', __name__, url_prefix='/private/order')

@private_order_bp.route('/delete_drawfail')
def delete_drawfail():
    orders=Order.query.filter(Order.status==0).all()
    for order in orders:
        order.delete()
    return '1'