import datetime

from sqlalchemy import or_

from app.model import Order, TimeTable, DrawTime
from exts import db, scheduler, cache
from utils.log import logger


def draw(drawtime_id):
    with scheduler.app.app_context():
        drawtime = DrawTime.get(drawtime_id)

        success_orders = Order.query.filter(Order.drawtime_id == drawtime.id,
                                            or_(Order.timetable_id != None, Order.timetable_id != '')).all()
        for success_order in success_orders:
            success_order.status = 1
            db.session.add(success_order)
            print(222222222222222)
            if success_order.book_num != 1:
                scheduler.add_job(
                    func=delorder,
                    trigger="date",
                    id=success_order.id,
                    args=(success_order.id,),
                    name=':'.join([drawtime.id, datetime.datetime.now().strftime('%Y-%m-%d %H:%M%S')]),
                    run_date=datetime.datetime.now() + datetime.timedelta(hours=1),
                    misfire_grace_time=60,
                    replace_existing=True,
                )

        timetables = TimeTable.query.filter(TimeTable.drawtime_id == drawtime.id, TimeTable.ticket_num > 0).all()
        for timetable in timetables:
            order = Order.query.filter(Order.drawtime_id == drawtime.id, Order.book_num == timetable.ticket_num,
                                       Order.book_num <= timetable.can_book_num, Order.status == 2).first()
            if order:
                order.timetable_id = timetable.id
                order.status = 1
                timetable.ticket_num = 0
                db.session.add(order)
                db.session.add(timetable)
                if order.book_num !=1:
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
            else:
                orders = Order.query.filter(Order.drawtime_id == drawtime.id, Order.book_num < timetable.ticket_num,
                                            Order.book_num <= timetable.can_book_num, Order.status == 2).all()

                for order in orders:
                    if timetable.ticket_num > 0 and timetable.ticket_num >= order.book_num:
                        timetable.ticket_num -= order.book_num
                        order.timetable_id = timetable.id
                        order.status = 1
                        db.session.add(order)
                        if order.book_num != 1:
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
                    if timetable.ticket_num <= 0:
                        break
                db.session.add(timetable)

        orders = Order.query.filter(Order.drawtime_id == drawtime.id, Order.status == 2).all()
        for order in orders:
            order.status = 0
            db.session.add(order)
        try:
            db.session.commit()
        except:
            logger.error('error_draw:' + drawtime.id)
        logger.info('success_draw:' + drawtime.id)
        return '1'


def delorder(order_id):
    with scheduler.app.app_context():
        db.session.commit()
        order = Order.query.with_for_update().get(order_id)
        if not order:
            return '0'
        if order.book_num != 1:
            timetable=TimeTable.query.get(order.timetable_id)
            child_orders = Order.query.filter(Order.parent_order_id == order.id).all()
            for child_order in child_orders:
                child_order.status=3
                timetable.ticket_num+=1
                db.session.add(child_order)
            order.status=3
            timetable.ticket_num+=order.book_num
            db.session.add(order)
            db.session.add(timetable)
            db.session.commit()
        return '1'


def make_ticketid(timetable_id):
    with scheduler.app.app_context():
        orders = Order.query.filter(Order.timetable_id == timetable_id, or_(Order.status == 1,Order.status==4)).order_by(
            Order.create_time).all()
        i = 1
        for order in orders:
            timetable = order.timetable
            cache.set('ticketid_%s' % order.id, i,
                      (timetable.end_time - datetime.datetime.now() + datetime.timedelta(minutes=5)).seconds)
            i += 1

    return '1'
