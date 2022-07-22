import datetime
import json
import uuid

from flask import Blueprint, request
from sqlalchemy import extract

from app.model import DrawTime, Place
from exts import db, scheduler
from scheduler_task.tasks import draw
from utils.http import render_json
from utils.time_form import to_ymdhfm

admin_drawtime_bp = Blueprint('admin_draw', __name__, url_prefix='/admin/drawtime')


@admin_drawtime_bp.route('/insert_port', methods=['POST'])
def add_post():
    try:
        data = json.loads(request.data)
        cycle_time = data.get('cycle_time', None)
    except:
        data = request.form
        cycle_time = data.getlist('cycle_time[]', None)

    draw_start_time = data.get('draw_start_time', None)
    draw_end_time = data.get('draw_end_time', None)
    book_start_time = data.get('book_start_time', None)
    book_end_time = data.get('book_end_time', None)
    place_id = data.get('place_id', None)

    if draw_start_time and draw_end_time and book_start_time and book_end_time and place_id:
        try:
            draw_start_time, draw_end_time, book_start_time, book_end_time = to_ymdhfm(draw_start_time, draw_end_time,
                                                                                       book_start_time, book_end_time)
        except:
            return render_json([], 2102, '日期格式错误')

        now = datetime.datetime.now()
        if draw_start_time <= now:
            return render_json([], 2103, '不能设置过去时间')

        if book_start_time < draw_start_time:
            return render_json([], 2402, '抽签时间不能大于预约时间')

        if draw_start_time >= draw_end_time or book_start_time >= book_end_time:
            return render_json([], 2101, '开始时间必须小于结束时间')

        drawtimes = DrawTime.query.filter(DrawTime.place_id==place_id,
                                          extract('year', DrawTime.draw_start_time) == draw_start_time.year,
                                          extract('month', DrawTime.draw_start_time) == draw_start_time.month,
                                          extract('day', DrawTime.draw_start_time) == draw_start_time.day).all()
        if drawtimes:
            return render_json([], 2401, '一天只能有一次抽签')

        place = Place.get(place_id)
        if not place:
            return render_json([], 1301, '没有指定场所')

        if place.parent_id != '-1':
            return render_json([], 2403, '请选择大场所')

        drawtime = DrawTime()
        drawtime.id = str(uuid.uuid4())
        drawtime.draw_start_time = draw_start_time
        drawtime.draw_end_time = draw_end_time
        drawtime.book_start_time = book_start_time
        drawtime.book_end_time = book_end_time
        drawtime.place_id = place.id
        if cycle_time:
            try:
                cycle_time.sort()
                drawtime.cycle_time = ','.join(cycle_time)
            except:
                return render_json([], 1000, '缺少参数')
        try:
            db.session.add(drawtime)
            db.session.commit()
        except:
            return render_json([], 1006, '数据库错误')

        scheduler.add_job(
            func=draw,
            trigger="date",
            id=drawtime.id,
            args=(drawtime.id,),
            name=':'.join([drawtime.id, now.strftime('%Y-%m-%d %H:%M%S')]),
            run_date=drawtime.draw_end_time + datetime.timedelta(minutes=1),
            misfire_grace_time=60,
            replace_existing=True,
        )
        return render_json([])

    else:
        return render_json([], 1000, '缺少参数')


@admin_drawtime_bp.route('/select_port')
def search_port():
    place_id = request.args.get('place_id')
    draw_start_time = request.args.get('draw_start_time')
    draw_end_time = request.args.get('draw_end_time')
    book_start_time = request.args.get('book_start_time')
    book_end_time = request.args.get('book_end_time')
    base = request.args.get('base', 'draw_start_time')
    sort_order = request.args.get('sort_order', 'desc')
    if not place_id:
        return render_json([], 1000, '缺少参数')

    drawtimes = DrawTime.query.filter(DrawTime.place_id == place_id)

    if draw_start_time:
        try:
            draw_start_time = datetime.datetime.strptime(draw_start_time, '%Y-%m-%d %H:%M:%S')
        except:
            return render_json([], 2102, '日期格式错误')

        drawtimes = drawtimes.filter(DrawTime.draw_start_time >= draw_start_time)

    if draw_end_time:
        try:
            draw_end_time = datetime.datetime.strptime(draw_end_time, '%Y-%m-%d %H:%M:%S')
        except:
            return render_json([], 2102, '日期格式错误')

        drawtimes = drawtimes.filter(DrawTime.draw_end_time <= draw_end_time)

    if book_start_time:
        try:
            book_start_time = datetime.datetime.strptime(book_start_time, '%Y-%m-%d %H:%M:%S')
        except:
            return render_json([], 2102, '日期格式错误')

        drawtimes = drawtimes.filter(DrawTime.book_start_time >= book_start_time)

    if book_end_time:
        try:
            book_end_time = datetime.datetime.strptime(book_end_time, '%Y-%m-%d %H:%M:%S')
        except:
            return render_json([], 2102, '日期格式错误')

        drawtimes = drawtimes.filter(DrawTime.draw_end_time <= book_end_time)

    if base:
        if not (sort_order == 'desc' or sort_order == 'asc'):
            return render_json([], 2405, 'sort_order选值错误')
        sort_base = 'DrawTime.%s.%s()' % (base, sort_order)
        try:
            drawtimes = drawtimes.order_by(eval(sort_base))
        except:
            return render_json([],2404,'base选值错误')

    datalist = []
    for drawtime in drawtimes.all():
        datalist.append(drawtime.to_detail_dict())

    return render_json(datalist)


@admin_drawtime_bp.route('delete_port')
def delete_port():
    drawtime_id = request.args.get('drawtime_id')
    if not drawtime_id:
        return render_json([], 1000, '缺少参数')

    drawtime = DrawTime.query.get(drawtime_id)
    if not drawtime:
        return render_json([], 2110, '没有指定的抽签时间表')
    try:
        drawtime.delete()
    except:
        return render_json([], 1006, '数据库错误')

    try:
        scheduler.remove_job(drawtime_id)
    except:
        pass

    return render_json([])


@admin_drawtime_bp.route('/update_port',methods=['POST'])
def update_port():
    try:
        data = json.loads(request.data)
        cycle_time = data.get('cycle_time', None)
    except:
        data = request.form
        cycle_time = data.getlist('cycle_time[]', None)

    id = data.get('id')
    draw_start_time = data.get('draw_start_time')
    draw_end_time = data.get('draw_end_time')
    book_start_time = data.get('book_start_time')
    book_end_time = data.get('book_end_time')

    if not (id and draw_start_time and draw_end_time and book_start_time and book_end_time):
        return render_json([], 1000, '缺少参数')

    try:
        draw_start_time, draw_end_time, book_start_time, book_end_time = to_ymdhfm(draw_start_time, draw_end_time,
                                                                                   book_start_time, book_end_time)
    except:
        return render_json([], 2102, '日期格式错误')

    if book_start_time < draw_start_time:
        return render_json([], 2402, '抽签时间不能大于预约时间')

    if draw_start_time >= draw_end_time or book_start_time >= book_end_time:
        return render_json([], 2101, '开始时间必须小于结束时间')

    drawtimes = DrawTime.query.filter(DrawTime.id != id,
                                      extract('year', DrawTime.draw_start_time) == draw_start_time.year,
                                      extract('month', DrawTime.draw_start_time) == draw_start_time.month,
                                      extract('day', DrawTime.draw_start_time) == draw_start_time.day).all()
    if drawtimes:
        print('-'*20,drawtimes)
        return render_json([], 2401, '一天只能有一次抽签')

    drawtime = DrawTime.query.get(id)
    if not drawtime:
        return render_json([], 2110, '没有指定的抽签时间表')

    timetables=drawtime.timetables()
    start_time=None
    if timetables:
        start_time=min(timetables, key=lambda x: x.start_time).start_time

    now = datetime.datetime.now()
    if now <= drawtime.draw_start_time:
        if draw_start_time<now:
            return render_json([], 2406, '抽签开始时间要比现在晚')
    elif drawtime.draw_start_time<now and now<=drawtime.draw_end_time:
        if not((draw_end_time-now).total_seconds()>=60):
            return render_json([], 2407, '抽签结束时间必须比现在要晚至少1分钟')
    elif drawtime.draw_end_time<now and now<=book_start_time:
        if book_start_time<now:
            return render_json([], 2408, '预约开始时间要比现在晚')
    elif drawtime.book_start_time<now and now<=book_end_time:
        if book_end_time<now:
            return render_json([],2409,'预约结束时间要比现在晚')
    elif (not start_time) or (drawtime.book_end_time<now and now<=start_time):
        if draw_start_time > now or draw_end_time > now or book_start_time>now:
            return render_json([],2410,'抽签及预约时间已过，只能延长预约结束时间')
    elif start_time and now>start_time:
        return render_json([],2411,'场所已经开始使用不能设置了')

    flag=0
    if drawtime.draw_end_time != draw_end_time:
        flag=1

    drawtime.draw_start_time = draw_start_time
    drawtime.draw_end_time = draw_end_time
    drawtime.book_start_time = book_start_time
    drawtime.book_end_time = book_end_time
    drawtime.cycle_time = cycle_time if cycle_time else None
    db.session.add(drawtime)
    # try:
    db.session.commit()
    # except:
    #     return render_json([], 1006, '数据库错误')

    if flag==1:
        try:
            scheduler.remove_job(drawtime.id)
        except:
            pass
        scheduler.add_job(
            func=draw,
            trigger="date",
            id=drawtime.id,
            args=(drawtime.id,),
            name=':'.join([drawtime.id, now.strftime('%Y-%m-%d %H:%M%S')]),
            run_date=drawtime.draw_end_time + datetime.timedelta(minutes=1),
            misfire_grace_time=60,
            replace_existing=True,
        )


    return render_json([])
