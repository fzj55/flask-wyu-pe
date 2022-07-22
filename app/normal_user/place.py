"""场所"""
import datetime

from flask import Blueprint, request

from app.model import Place, DrawTime, TimeTable, Order
from utils.http import render_json
from utils.mysort import name_sort

place_bp = Blueprint('place', __name__, url_prefix='/place')
 

@place_bp.route('/open_port')
def open_port():
    """开放场所"""
    open_time=request.args.get('open_time',0)
    datalist = []
    places = Place.query.filter(Place.parent_id == -1).all()

    for place in places:
        data = place.to_dict()
        now=datetime.datetime.now()
        if not open_time:
            drawtime=DrawTime.get_today(place.id)
        else:
            drawtime = DrawTime.get_yesterday(place.id)
        if drawtime:
            data['draw_start_time']=drawtime.draw_start_time.strftime("%Y-%m-%d %H:%M:%S")
            data['draw_end_time']=drawtime.draw_end_time.strftime("%Y-%m-%d %H:%M:%S")
            data['book_start_time'] = drawtime.book_start_time.strftime("%Y-%m-%d %H:%M:%S")
            data['book_end_time'] = drawtime.book_end_time.strftime("%Y-%m-%d %H:%M:%S")
            if drawtime.draw_start_time<=now and drawtime.draw_end_time>=now:
                timetabels=drawtime.timetables()
                if timetabels:
                    max_book_num=max(timetabels,key=lambda x:x.can_book_num).can_book_num
                    data['max_book_num']=max_book_num
        datalist.append(data)
    return render_json(datalist)

# @place_bp.route('/time_port')
# def time_port():
#     """场所时间表"""
#     datalist = []
#     id = request.args.get('id', None)
#     if id:
#         now = datetime.datetime.now()
#         drawtime = DrawTime.query.filter(DrawTime.place_id == id, DrawTime.draw_start_time <= now,
#                                          DrawTime.draw_end_time >= now).first()
#         timetables = drawtime.timetables()
#         if timetables:
#             for timetable in timetables:
#                 datalist.append(timetable.to_dict(is_array=True))
#             return render_json(datalist, 1)
#         else:
#             return render_json(datalist, 1302, '暂未开启预约，请移步公共栏查看')
#     else:
#         return render_json(datalist, 1000, '缺少参数')

@place_bp.route('/detail_port')
def detail_port():
    """订单详情（补选）"""
    place_id = request.args.get('place_id', None)

    if place_id:
        datadict = {}
        datadict['detail'] = []

        place = Place.get(place_id)
        if not place:
            return render_json([], 1301, '没有指定场所')

        drawtime = DrawTime.get_yesterday(place.id)
        if not drawtime:
            return render_json([], 1303, '今天没有设置抽签时间')
        datadict['drawtime'] = drawtime.to_dict()

        places = Place.query.filter(Place.parent_id == drawtime.place_id and Place.is_open == True).all()

        if places:
            places.sort(key=lambda x:name_sort(x.name))
            time_set = set()
            for place in places:
                data, time_data = place.to_detail_dict(drawtime.id)
                datadict['detail'].append(data)
                print('-' * 20, time_set)
                for time in time_data:
                    time_set.add(time)
            time_list = list(time_set)
            time_list.sort()
            datadict['time'] = time_list
            return render_json(datadict, 1)
        else:
            timetables = drawtime.timetables()
            time_set = set()
            for timetable in timetables:
                date = timetable.start_time.strftime("%Y-%m-%d")
                time = '-'.join([timetable.start_time.strftime("%H:%M"), timetable.end_time.strftime("%H:%M")])
                time = ' '.join([date, time])
                time_set.add(time)
                timetable_data = timetable.to_dict(0, True, 'cycle_time', 'initial_ticket_num')
                timetable_data['time'] = time
                datadict['detail'].append(timetable_data)
            time_list = list(time_set)
            time_list.sort()
            datadict['time'] = time_list
            return render_json(datadict)
    else:
        return render_json([], 1000, '缺少参数')
