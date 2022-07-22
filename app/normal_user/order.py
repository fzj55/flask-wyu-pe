import datetime
import json
import random
import uuid

from flask import Blueprint, g, request
from sqlalchemy import or_

from app.model import TimeTable, Order, Place, DrawTime
from exts import db, cache, scheduler
from scheduler_task.tasks import delorder
from utils.http import render_json
from utils.log import logger

order_bp = Blueprint('order', __name__, url_prefix='/order')


@order_bp.route('/joindraw_port', methods=['POST'])
def joindraw_port():
    """参与抽签"""
    try:
        data = json.loads(request.data)
    except:
        data = request.form

    place_id = data.get('place_id', None)
    book_num = data.get('book_num', None)

    if not place_id or not book_num:
        return render_json([], 1000, '缺少参数')

    book_num = int(book_num)

    now = datetime.datetime.now()
    drawtime = DrawTime.query.filter(DrawTime.place_id == place_id, DrawTime.draw_start_time <= now,
                                     DrawTime.draw_end_time >= now).first()
    if not drawtime:
        return render_json([], 1501, '未到参与抽签时间')

    residue_num = g.user.get_residue_degree(drawtime.place_id)
    if residue_num <= 0:
        return render_json([], 1407, '预约达到上限')

    old_order = Order.query.filter(Order.user_id == g.user.id, Order.drawtime_id == drawtime.id).first()
    if old_order:
        return render_json([], 1404, '今天已经参加过抽签')
    parent_place = Place.get(place_id)
    places = parent_place.children()
    if places:
        random.shuffle(places)
        for place in places:
            db.session.commit()
            timetable = TimeTable.query.filter(TimeTable.place_id == place.id, TimeTable.drawtime_id == drawtime.id,
                                               TimeTable.ticket_num >= book_num,
                                               TimeTable.can_book_num >= book_num).with_for_update().first()
            if timetable:
                break
        else:
            timetable = None
    else:
        db.session.commit()
        timetable = TimeTable.query.filter(TimeTable.place_id == parent_place.id, TimeTable.drawtime_id == drawtime.id,
                                           TimeTable.ticket_num >= book_num,
                                           TimeTable.can_book_num >= book_num).with_for_update().first()

    random_num = random.randint(0, 2)
    if random_num >= 1 and timetable:
        timetable.ticket_num -= book_num
        order = Order()
        order.id = str(uuid.uuid4())
        order.user_id = g.user.id
        order.timetable_id = timetable.id
        order.drawtime_id = drawtime.id
        order.create_time = now
        order.book_num = book_num
        order.status = 2
        order.parent_order_id = '-1'
        db.session.add(timetable)
        logger.info(' && '.join([g.user.name, drawtime.id, timetable.id, str(timetable.ticket_num), order.id]))
    else:
        order = Order()
        order.id = str(uuid.uuid4())
        order.user_id = g.user.id
        order.drawtime_id = drawtime.id
        order.create_time = now
        order.book_num = book_num
        order.status = 2
        order.parent_order_id = '-1'
        logger.info(' || '.join([g.user.name, drawtime.id, order.id]))
    db.session.add(order)
    try:
        db.session.commit()
    except:
        return render_json([], 1006, '数据库错误')
    return render_json([])


@order_bp.route('/draworder_port')
def draworder_port():
    """抽签查询"""
    datalist = []
    orders = Order.query.filter(Order.user_id == g.user.id,or_(Order.status==0,Order.status==1,Order.status==2)).all()
    if orders:
        for order in orders:
            datalist.append(order.to_detail_dict())
        datalist.sort(key=lambda x: datetime.datetime.strptime(x['drawtime']['draw_start_time'], '%Y-%m-%d %H:%M:%S'),
                      reverse=True)
        return render_json(datalist)
    else:
        return render_json([], 1403, '暂无订单')


@order_bp.route('/order_port')
def order_port():
    """订单查询"""
    datalist = []
    orders = Order.query.filter(Order.user_id == g.user.id, or_(Order.status == 1,Order.status==4)).all()
    if orders:
        for order in orders:
            datalist.append(order.to_detail_dict())
        datalist.sort(key=lambda x: datetime.datetime.strptime(x['timetable']['start_time'], '%Y-%m-%d %H:%M:%S'),
                      reverse=True)
        return render_json(datalist)
    else:
        return render_json([], 1403, '暂无订单')


@order_bp.route('/del_order_port')
def del_order_port():
    id = request.args.get('id', None)
    if id:
        order = Order.query.filter(Order.id == id, Order.user_id == g.user.id, Order.parent_order_id == '-1').first()
        if order:
            now = datetime.datetime.now()
            drawtime = DrawTime.get(order.drawtime_id)
            if order.status == 2:
                if drawtime.draw_start_time > now or drawtime.draw_end_time < now:
                    return render_json([], 1408, '不能取消抽签')
                if order.timetable_id:
                    timetable = TimeTable.query.get(order.timetable_id)
                    timetable.ticket_num += order.book_num
                    db.session.add(timetable)
                    try:
                        db.session.commit()
                    except:
                        return render_json([], 1006, '数据库错误')
                try:
                    order.delete()
                except:
                    return render_json([], 1006, '数据库错误')

            elif order.status == 1 or order.status==4:
                if drawtime.book_start_time > now or drawtime.book_end_time < now:
                    return render_json([], 1406, '不能取消预定了')
                timetable = TimeTable.query.get(order.timetable_id)
                timetable.ticket_num += order.book_num
                order.status = 3
                child_orders=Order.query.filter(Order.parent_order_id==order.id,Order.status==4).all()
                for child_order in child_orders:
                    timetable.ticket_num+=1
                    child_order.status = 3
                    db.session.add(child_order)
                db.session.add(timetable)
                db.session.add(order)
                try:
                    db.session.commit()
                except:
                    return render_json([], 1006, '数据库错误')
            else:
                return render_json([], 1004, '非法尝试')

            if order.book_num !=1:
                try:
                    scheduler.remove_job(order.id)
                except:
                    pass

            return render_json([])

        else:
            return render_json([], 1004, '非法尝试')
    else:
        return render_json([], 1000, '缺少参数')


@order_bp.route('/book_port', methods=['POST'])
def book_port():
    try:
        data = json.loads(request.data)
    except:
        data = request.form

    timetable_id = data.get('timetable_id')
    book_num = int(data.get('book_num',0))

    if not timetable_id or not book_num:
        return render_json([], 1000, '缺少参数')

    db.session.commit()
    timetable = TimeTable.query.filter(TimeTable.id == timetable_id,TimeTable.can_book_num>=book_num,
                                       TimeTable.ticket_num >= book_num).with_for_update().first()

    if not timetable:
        return render_json([], 1401, '没有此时间表')

    drawtime = timetable.drawtime
    now = datetime.datetime.now()
    if not (drawtime.book_start_time <= now and drawtime.book_end_time >= now):
        return render_json([], 1405, '不在预定时间范围内')

    if g.user.is_reserved(timetable.drawtime_id):
        return render_json([], 1411, '今天已经预定过了')

    residue_num = g.user.get_residue_degree(drawtime.place_id)
    if residue_num <= 0:
        return render_json([], 1407, '预约达到上限')

    order = Order()
    order.id = str(uuid.uuid4())
    order.create_time = datetime.datetime.now()
    order.user_id = g.user.id
    order.drawtime_id = drawtime.id
    order.timetable_id = timetable.id
    order.book_num = book_num
    order.status = 4
    order.parent_order_id= '-1'
    timetable.ticket_num -= book_num
    db.session.add(order)
    db.session.add(timetable)
    if book_num!=1:
        scheduler.add_job(
            func=delorder,
            trigger="date",
            id=order.id,
            args=(order.id,),
            name=':'.join([drawtime.id, datetime.datetime.now().strftime('%Y-%m-%d %H:%M%S')]),
            run_date=datetime.datetime.now() + datetime.timedelta(hours=1),
            misfire_grace_time=60,
            replace_existing=True,
        )

    try:
        db.session.commit()
    except:
        return render_json([], 1006, '数据库错误')

    return render_json([])


@order_bp.route('/inviteuser_port', methods=['POST'])
def inviteuser_port():
    try:
        data = json.loads(request.data)
    except:
        data = request.form

    order_id = data.get('order_id')
    auth_codelist = data.get('auth_codelist')
    if not auth_codelist or not order_id:
        return render_json([], 1000, '缺少参数')

    db.session.commit()
    parent_order = Order.query.with_for_update().get(order_id)
    if not parent_order:
        return render_json([], 1410, '没有此订单')
    if len(auth_codelist) >= parent_order.book_num:
        return render_json([], 1412, '输入授权码个数不能大于订单预定人数')
    if parent_order.status != 1 and parent_order.status!=4:
        return render_json([], 1004, '非法尝试')

    drawtime = parent_order.drawtime

    authcode_error = []
    already_book = []
    no_residue = []
    for auth_code in auth_codelist:
        user = cache.get('authcode:%s' % auth_code)
        if not user:
            authcode_error.append(auth_code)
            continue

        if user.is_reserved(parent_order.drawtime_id):
            already_book.append(user.name)
            continue

        residue_num = user.get_residue_degree(drawtime.place_id)
        if residue_num <= 0:
            no_residue.append(user.name)
            continue

        order = Order()
        order.id = str(uuid.uuid4())
        order.user_id = user.id
        order.timetable_id = parent_order.timetable_id
        order.drawtime_id = parent_order.drawtime_id
        order.create_time = datetime.datetime.now()
        order.book_num = 1
        order.status = 4
        order.parent_order_id = parent_order.id
        db.session.add(order)

    parent_order.book_num = parent_order.book_num - len(auth_codelist) + len(authcode_error) + len(already_book) + len(
        no_residue)
    db.session.add(parent_order)
    try:
        db.session.commit()
    except Exception as e:
        logger.info(e)
        return render_json([], 1006, '数据库错误')
    if authcode_error or already_book:
        return render_json({'authcode_error': authcode_error, 'already_book': already_book, 'no_residue': no_residue},
                           1413, '部分用户加入失败，无问题用户已经加入')
    return render_json([])


@order_bp.route('/search_childorder_port')
def search_childorder_port():
    order_id = request.args.get('order_id')
    if not order_id:
        return render_json([], 1000, '缺少参数')

    order = Order.get(order_id)
    if not order:
        return render_json([], 1410, '没有此订单')
    if order.user.id != g.user.id:
        return render_json([], 1004, '非法尝试')

    orders = Order.query.filter(Order.parent_order_id == order.id, Order.status == 4).all()
    data = []
    for order in orders:
        data.append({'childorder_id': order.id, 'belong_username': order.user.name})
    return render_json(data)


@order_bp.route('/del_childorder_port')
def del_childorder_port():
    parent_order_id = request.args.get('parent_order_id')
    child_order_id = request.args.get('child_order_id')

    if not parent_order_id or not child_order_id:
        return render_json([], 1000, '缺少参数')

    parent_order = Order.query.get(parent_order_id)
    if not parent_order:
        return render_json([], 1410, '没有此订单')
    if parent_order.user.id != g.user.id:
        return render_json([], 1004, '非法尝试')

    child_order = Order.query.get(child_order_id)
    if not child_order:
        return render_json([], 1410, '没有此订单')
    if parent_order.id != child_order.parent_order_id:
        return render_json([], 1004, '非法尝试')

    if datetime.datetime.now() > parent_order.drawtime.book_end_time:
        return render_json([], 1406, '不能取消预定了')

    parent_order.book_num += 1
    db.session.delete(child_order)
    cache.delete('Model:Order:%s' % child_order.id)
    db.session.add(parent_order)
    try:
        db.session.commit()
    except:
        return render_json([], 1006, '数据库错误')
    return render_json([])