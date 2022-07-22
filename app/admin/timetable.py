"""管理场所"""
import datetime
import json
import os
import uuid

from flask import Blueprint, request, send_file

from app.model import TimeTable, Place, DrawTime
from exts import db, scheduler, cache
from scheduler_task.tasks import make_ticketid
from settings import Config
from utils.http import render_json
from utils.make_excel import make_timetable
from utils.mysort import name_sort

admin_timetable_bp = Blueprint('admin_timetable', __name__, url_prefix='/admin/timetable')


@admin_timetable_bp.route('/insert_port', methods=['POST'])
def insert_port():
    try:
        data = json.loads(request.data)
        place_ids = data.get('place_ids')
        # cycle_time = data.get('cycle_time', None)
    except:
        data = request.form
        place_ids = data.getlist('place_ids[]')
        # cycle_time = data.getlist('cycle_time[]', None)
    # draw_start_time = data.get('draw_start_time', None)
    # draw_end_time = data.get('draw_end_time', None)
    # book_start_time = data.get('book_start_time', None)
    # book_end_time = data.get('book_end_time', None)
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    ticket_num = int(data.get('ticket_num'))
    can_book_num = int(data.get('can_book_num'))
    is_follow_cycle = data.get('is_follow_cycle')
    drawtime_id = data.get('drawtime_id')

    print('=' * 20)
    print(place_ids)
    print(start_time)
    print(end_time)
    # print(book_start_time)
    # print(book_end_time)
    print(ticket_num)
    print(can_book_num)
    # print(cycle_time)
    # print(type(cycle_time))

    try:
        start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        # book_start_time = datetime.datetime.strptime(book_start_time, '%Y-%m-%d %H:%M:%S')
        # book_end_time = datetime.datetime.strptime(book_end_time, '%Y-%m-%d %H:%M:%S')
        # draw_start_time = datetime.datetime.strptime(draw_start_time, '%Y-%m-%d %H:%M:%S')
        # draw_end_time = datetime.datetime.strptime(draw_end_time, '%Y-%m-%d %H:%M:%S')
    except:
        return render_json([], 2102, '日期格式错误')

    if not (
            place_ids and start_time and end_time and ticket_num and can_book_num and is_follow_cycle and drawtime_id):  # and book_start_time and book_end_time and draw_start_time and draw_end_time
        return render_json([], 1000, '缺少参数')

    is_follow_cycle = int(is_follow_cycle)

    drawtime = DrawTime.get(drawtime_id)
    if not drawtime:
        return render_json([], 2110, '没有指定的抽签时间表')

    if not ((start_time - drawtime.book_end_time).total_seconds() > 1800):
        return render_json([], 2113, '开始使用时间必须比预定结束时间晚30分钟')

    if start_time >= end_time:  # and book_start_time < book_end_time and draw_start_time < draw_end_time
        return render_json([], 2101, '开始时间必须小于结束时间')

    now = datetime.datetime.now()
    tasklist=[]
    for id in place_ids:
        if start_time <= now:  # or book_start_time <= now or draw_start_time <= now
            return render_json([], 2103, '不能设置过去时间')

        # if book_start_time >= start_time or book_end_time >= start_time:
        #     return render_json(error, 2107, '预定开始或结束时间不能大于场地开始使用时间')

        # if draw_start_time >= book_start_time or draw_end_time >= book_end_time:
        #     return render_json(error, 2109, '抽签开始或结束时间不能大于预约开始时间')

        if can_book_num > ticket_num:
            return render_json([], 2106, '票数或初始票数小于一个人一次能预定数量')

        # timetables = TimeTable.query.filter(extract('year', TimeTable.draw_start_time) == draw_start_time.year,
        #                                    extract('month', TimeTable.draw_start_time) == draw_start_time.month,
        #                                    extract('day',TimeTable.draw_start_time) == draw_start_time.day).all()
        # if timetables:
        #     return render_json([], 2401, '一天只能有一次抽签')

        timetable = TimeTable()
        timetable.id = str(uuid.uuid4())
        timetable.place_id = id
        timetable.start_time = start_time
        timetable.end_time = end_time
        # timetable.book_start_time = book_start_time
        # timetable.book_end_time = book_end_time
        # timetable.draw_start_time = draw_start_time
        # timetable.draw_end_time = draw_end_time
        timetable.ticket_num = ticket_num
        timetable.initial_ticket_num = ticket_num
        timetable.is_follow_cycle = is_follow_cycle
        timetable.can_book_num = can_book_num
        timetable.initial_ticket_num = ticket_num
        timetable.drawtime_id = drawtime_id
        # timetable.can_book_many = True if can_book_num > 1 else False
        db.session.add(timetable)

        scheduler.add_job(
            func=make_ticketid,
            trigger="date",
            id=timetable.id,
            args=(timetable.id,),
            name=timetable.id,
            run_date=drawtime.book_end_time + datetime.timedelta(minutes=1),
            misfire_grace_time=60,
            replace_existing=True,
        )
        tasklist.append(timetable.id)
    try:
        db.session.commit()
    except Exception as e:
        print(e)
        for i in tasklist:
            scheduler.remove_job(i)
        return render_json([], 1006, '数据库错误')

    # if error:
    #     return render_json(error, 2104, '部分场所添加的时间与原有的冲突')
    return render_json([])


@admin_timetable_bp.route('/select_port')
def select_port():
    place_id = request.args.get('place_id')
    drawtime_id = request.args.get('drawtime_id')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    base = request.args.get('base', 'start_time')
    sort_order = request.args.get('sort_order', 'desc')
    if not place_id:
        return render_json([], 1000, '缺少参数')

    if start_time:
        try:
            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        except:
            return render_json([], 2102, '日期格式错误')

    if end_time:
        try:
            end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        except:
            return render_json([], 2102, '日期格式错误')

    base_timetables=TimeTable.query
    if drawtime_id:
        base_timetables=base_timetables.filter(TimeTable.drawtime_id==drawtime_id)

    datalist = []
    parent_places = Place.query.filter(Place.parent_id == place_id).all()
    if parent_places:
        for place in parent_places:
            timetables = base_timetables.filter(TimeTable.place_id == place.id)
            if start_time:
                timetables = timetables.filter(TimeTable.start_time >= start_time)
            if end_time:
                timetables = timetables.filter(TimeTable.start_time <= end_time)
            for timetable in timetables.all():
                data = timetable.to_dict()
                data['name'] = place.name
                datalist.append(data)
    else:
        if base == 'name':
            return render_json([], 2111, '无法根据base字段排序')
        timetables = base_timetables.filter(TimeTable.place_id == place_id)
        if start_time:
            timetables = timetables.filter(TimeTable.start_time >= start_time)
        if end_time:
            timetables = timetables.filter(TimeTable.start_time <= end_time)
        for timetable in timetables.all():
            datalist.append(timetable.to_dict())

    try:
        if base == 'name':
            datalist.sort(key=lambda x: name_sort(x['name']), reverse=False if sort_order == 'asc' else True)
        else:
            datalist.sort(key=lambda x: x[base], reverse=False if sort_order == 'asc' else True)
    except:
        return render_json([], 2112, 'base字段或sort_order字段值错误')
    return render_json(datalist)


@admin_timetable_bp.route('/update_port', methods=['POST'])
def update_time_port():
    try:
        data = json.loads(request.data)
        # cycle_time = data.get('cycle_time', None)
    except:
        data = request.form
        # cycle_time = data.getlist('cycle_time[]', None)
    # draw_start_time = data.get('draw_start_time', None)
    # draw_end_time = data.get('draw_end_time', None)
    # book_start_time = data.get('book_start_time', None)
    # book_end_time = data.get('book_end_time', None)
    id = data.get('id')
    place_id = data.get('place_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    ticket_num = int(data.get('ticket_num'))
    can_book_num = int(data.get('can_book_num'))
    is_follow_cycle = data.get('is_follow_cycle')
    initial_ticket_num = data.get('initial_ticket_num')
    drawtime_id = data.get('drawtime_id')

    print('=' * 20)
    print(place_id)
    print(start_time)
    print(end_time)
    # print(book_start_time)
    # print(book_end_time)
    print(ticket_num)
    print(can_book_num)
    # print(cycle_time)
    # print(type(cycle_time))

    now = datetime.datetime.now()
    timetable = TimeTable.query.get(id)
    if not timetable:
        return render_json([], 1401, '没有此时间表')
    if timetable.start_time <= now:
        return render_json([], 2411, '场所已经开始使用不能设置了')

    try:
        start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        # book_start_time = datetime.datetime.strptime(book_start_time, '%Y-%m-%d %H:%M:%S')
        # book_end_time = datetime.datetime.strptime(book_end_time, '%Y-%m-%d %H:%M:%S')
        # draw_start_time = datetime.datetime.strptime(draw_start_time, '%Y-%m-%d %H:%M:%S')
        # draw_end_time = datetime.datetime.strptime(draw_end_time, '%Y-%m-%d %H:%M:%S')
    except:
        return render_json([], 2102, '日期格式错误')

    if not (place_id and start_time and end_time and ticket_num and can_book_num
            and is_follow_cycle and drawtime_id and id and initial_ticket_num):  # and book_start_time and book_end_time and draw_start_time and draw_end_time
        return render_json([], 1000, '缺少参数')

    drawtime = DrawTime.get(drawtime_id)
    if not drawtime:
        return render_json([], 2110, '没有指定的抽签时间表')

    if not ((start_time - drawtime.book_end_time).total_seconds() > 1800):
        return render_json([], 2113, '开始使用时间必须比预定结束时间晚30分钟')

    place = Place.get(place_id)
    if not place:
        return render_json([], 1301, '没有指定场所')

    if start_time >= end_time:  # and book_start_time < book_end_time and draw_start_time < draw_end_time
        return render_json([], 2101, '开始时间必须小于结束时间')

    if start_time <= now:  # or book_start_time <= now or draw_start_time <= now
        return render_json([], 2103, '不能设置过去时间')

    # if book_start_time >= start_time or book_end_time >= start_time:
    #     return render_json(error, 2107, '预定开始或结束时间不能大于场地开始使用时间')

    # if draw_start_time >= book_start_time or draw_end_time >= book_end_time:
    #     return render_json(error, 2109, '抽签开始或结束时间不能大于预约开始时间')

    if can_book_num > ticket_num:
        return render_json([], 2106, '票数或初始票数小于一个人一次能预定数量')

    # timetables = TimeTable.query.filter(extract('year', TimeTable.draw_start_time) == draw_start_time.year,
    #                                    extract('month', TimeTable.draw_start_time) == draw_start_time.month,
    #                                    extract('day',TimeTable.draw_start_time) == draw_start_time.day).all()
    # if timetables:
    #     return render_json([], 2401, '一天只能有一次抽签')

    timetable.place_id = place.id
    timetable.start_time = start_time
    timetable.end_time = end_time
    # timetable.book_start_time = book_start_time
    # timetable.book_end_time = book_end_time
    # timetable.draw_start_time = draw_start_time
    # timetable.draw_end_time = draw_end_time
    timetable.ticket_num = ticket_num
    timetable.initial_ticket_num = ticket_num
    timetable.is_follow_cycle = is_follow_cycle
    timetable.can_book_num = can_book_num
    timetable.initial_ticket_num = initial_ticket_num
    timetable.drawtime_id = drawtime_id
    # timetable.can_book_many = True if can_book_num > 1 else False
    db.session.add(timetable)
    try:
        db.session.commit()
    except:
        return render_json([], 1006, '数据库错误')
    # if error:
    #     return render_json(error, 2104, '部分场所添加的时间与原有的冲突')
    return render_json([])


@admin_timetable_bp.route('/delete_port')
def delete_port():
    id = request.args.get('id', None)
    if not id:
        return render_json([], 1000, '缺少参数')

    timetable = TimeTable.query.get(id)
    if not timetable:
        return render_json([], 2110, '没有指定的抽签时间表')

    try:
        timetable.delete()
    except:
        return render_json([], 1006, '数据库错误')

    return render_json([])


@admin_timetable_bp.route('/timetable_port')
def timetable_port():
    place_id = request.args.get('place_id', None)
    date = request.args.get('date')

    if not place_id:
        return render_json([], 1000, '缺少参数')

    if not date:
        date = datetime.date.today()

    if not isinstance(date, datetime.date):
        date = datetime.datetime.strptime(date, '%Y-%m-%d')

    place = Place.get(place_id)
    if not place:
        return render_json([], 1004, '非法尝试')

    data = {}
    children_place = place.children()
    children_place.sort(key=lambda x: name_sort(x.name))
    if children_place:
        for place in children_place:
            data[place.name] = {}
            timetables = TimeTable.query.filter(TimeTable.place_id == place.id,
                                                TimeTable.start_time > date,
                                                TimeTable.start_time < (date + datetime.timedelta(days=1))).order_by(
                TimeTable.start_time).all()

            for timetable in timetables:
                print('-' * 20, timetable.start_time)
                data[place.name][timetable.id] = {}
                data[place.name][timetable.id]['start_time'] = timetable.start_time
                data[place.name][timetable.id]['end_time'] = timetable.end_time
                data[place.name][timetable.id]['users'] = {}
                success_orders = timetable.success_orders()
                for order in success_orders:
                    ticketid = cache.get('ticketid_%s' % order.id)
                    if not ticketid:
                        ticketid=uuid.uuid4()
                    data[place.name][timetable.id]['users'][ticketid] = []
                    for num in range(order.book_num):
                        data[place.name][timetable.id]['users'][ticketid].append(order.user.name)
        name = make_timetable(data)
        return send_file(os.path.join(Config.STATIC_DIR, 'excel', name), as_attachment=True,
                         mimetype='application/vnd.ms-excel')
    else:
        timetables = TimeTable.query.filter(TimeTable.place_id == place.id,
                                            TimeTable.start_time > date,
                                            TimeTable.start_time < (date + datetime.timedelta(days=1))).order_by(
            TimeTable.start_time).all()

        if timetables:
            data[place.name] = {}
            for timetable in timetables:
                data[place.name][timetable.id] = {}
                data[place.name][timetable.id]['start_time'] = timetable.start_time
                data[place.name][timetable.id]['end_time'] = timetable.end_time
                data[place.name][timetable.id]['users'] = {}
                success_orders=timetable.success_orders()
                for order in success_orders:
                    ticketid = cache.get('ticketid_%s' % order.id)
                    if not ticketid:
                        ticketid=uuid.uuid4()
                    data[place.name][timetable.id]['users'][ticketid] = []
                    for num in range(order.book_num):
                        data[place.name][timetable.id]['users'][ticketid].append(order.user.name)
            name = make_timetable(data)
            return send_file(os.path.join(Config.STATIC_DIR, 'excel', name), as_attachment=True,
                             mimetype='application/vnd.ms-excel')
        else:
            render_json([], 2105, '此场所没有设置时间')


@admin_timetable_bp.route('/searchorder_port')
def searchorder_port():
    timetabel_id = request.args.get('timetabel_id')
    timetable = TimeTable.get(timetabel_id)
    if not timetable:
        return render_json([], 1401, '没有此时间表')
    orders = timetable.orders()
    data = []
    for order in orders:
        orderdetail = order.to_detail_dict()
        orderdetail['user'] = order.user.to_dict()
        data.append(orderdetail)
    return render_json(data)
