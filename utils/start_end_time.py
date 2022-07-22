import datetime


def get_week_start_end_time():
    weekday=datetime.date.today().weekday()
    end=6-weekday
    start_time=datetime.date.today()-datetime.timedelta(days=weekday)
    end_time=datetime.date.today()+datetime.timedelta(days=end+1)
    return start_time,end_time

def get_day_start_end_time():
    now_date=datetime.date.today()
    return now_date,now_date+datetime.timedelta(days=1)