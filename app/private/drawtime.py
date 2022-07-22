import datetime
import uuid

from flask import Blueprint, request
from sqlalchemy import or_

from app.model import TimeTable, DrawTime, Order
from exts import db, scheduler
from scheduler_task.tasks import draw, make_ticketid
from utils.http import render_json
from utils.start_end_time import get_week_start_end_time

private_drawtime_bp = Blueprint('private_drawtime', __name__, url_prefix='/private/drawtime')


@private_drawtime_bp.route('/cycle_time')
def cycle_time():
    # 注意：开始与结束的间隔不能超过一天
    day = str(datetime.date.today().weekday())
    date = datetime.date.today().strftime('%Y-%m-%d')
    drawtimes = DrawTime.query.filter(DrawTime.cycle_time != None, DrawTime.cycle_time != '').all()
    for drawtime in drawtimes:
        if day in drawtime.cycle_time:
            if date == drawtime.draw_start_time.strftime('%Y-%m-%d'):
                continue
            interval_draw_start_end = drawtime.draw_end_time - drawtime.draw_start_time
            interval_draw_book_start = drawtime.book_start_time - drawtime.draw_start_time
            interval_draw_book_end = drawtime.book_end_time - drawtime.draw_start_time

            new_drawtime = DrawTime()
            new_drawtime.id = str(uuid.uuid4())
            new_drawtime.draw_start_time = datetime.datetime.strptime(
                ' '.join([date, drawtime.draw_start_time.strftime('%H:%M:%S')]), '%Y-%m-%d %H:%M:%S')
            new_drawtime.draw_end_time = new_drawtime.draw_start_time + interval_draw_start_end
            new_drawtime.book_start_time = new_drawtime.draw_start_time + interval_draw_book_start
            new_drawtime.book_end_time = new_drawtime.draw_start_time + interval_draw_book_end
            new_drawtime.cycle_time = drawtime.cycle_time
            new_drawtime.place_id = drawtime.place_id
            db.session.add(new_drawtime)
            scheduler.add_job(
                func=draw,
                trigger="date",
                id=new_drawtime.id,
                args=(new_drawtime.id,),
                name=':'.join([new_drawtime.id, datetime.datetime.now().strftime('%Y-%m-%d %H:%M%S')]),
                run_date=new_drawtime.draw_end_time + datetime.timedelta(minutes=1),
                misfire_grace_time=60,
                replace_existing=True,
            )

            drawtime.cycle_time = None
            db.session.add(drawtime)

            timetables = TimeTable.query.filter(TimeTable.drawtime_id == drawtime.id).all()
            for timetable in timetables:
                if timetable.is_follow_cycle:
                    interval_draw_time_start = timetable.start_time - drawtime.draw_start_time
                    interval_draw_time_end = timetable.end_time - drawtime.draw_start_time

                    new_timetable = TimeTable()
                    new_timetable.id = str(uuid.uuid4())
                    new_timetable.start_time = new_drawtime.draw_start_time + interval_draw_time_start
                    new_timetable.end_time = new_drawtime.draw_start_time + interval_draw_time_end
                    new_timetable.ticket_num = timetable.initial_ticket_num
                    new_timetable.can_book_num = timetable.can_book_num
                    new_timetable.initial_ticket_num = timetable.initial_ticket_num
                    new_timetable.place_id = timetable.place_id
                    new_timetable.drawtime_id = new_drawtime.id
                    new_timetable.is_follow_cycle=timetable.is_follow_cycle
                    db.session.add(new_timetable)

                    scheduler.add_job(
                        func=make_ticketid,
                        trigger="date",
                        id=new_timetable.id,
                        args=(new_timetable.id,),
                        name=new_timetable.id,
                        run_date=new_drawtime.book_end_time + datetime.timedelta(minutes=1),
                        misfire_grace_time=60,
                        replace_existing=True,
                    )

    db.session.commit()
    return render_json([])


@private_drawtime_bp.route('/remove_timeout')
def remove_timeout_port():
    weekstart, weekend = get_week_start_end_time()
    flag = 0
    drawtimes = DrawTime.query.all()
    for drawtime in drawtimes:
        timetables = TimeTable.query.filter(TimeTable.drawtime_id == drawtime.id).all()
        for timetable in timetables:
            if timetable.end_time > datetime.datetime.strptime(' '.join([weekstart.strftime('%Y-%m-%d'), "00:00:00"]),
                                                               '%Y-%m-%d %H:%M:%S'):
                flag=1
            else:
                timetable.remove()
        if flag != 1:
            drawtime.delete()
        if flag == 1:
            flag = 0
    return render_json([])
