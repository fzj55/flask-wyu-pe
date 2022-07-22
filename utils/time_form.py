import datetime


def to_ymdhfm(*args):
    data=[]
    for time in args:
        data.append(datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S'))
    return data
