from datetime import datetime

import redis
import requests

# resp=requests.get('http://127.0.0.1:5000/private/user/check')
from redis import Redis

# from utils.cache import rds
#
# pyredis = Redis(host='127.0.0.1', port=6379, db=0)
# a=pyredis.set('shop',2)
# b=pyredis.setnx('shop',2)
# print(a,b)
# print(rds.llen('li'))
# p=rds.pipeline()
# a=rds.lpop('list')
# b=rds.lpop('list')
# c=rds.lpop('list')
# print(a,b,c)
# if rds.llen('li')==3:
#     print('-------------------')
#     p.execute()
# a=rds.lrange('li',0,4)
# print(a)
#
# import threading
# import time
# k=[]
# exitFlag = 0
#
# class myThread (threading.Thread):
#     def __init__(self, threadID, name, delay):
#         threading.Thread.__init__(self)
#         self.threadID = threadID
#         self.name = name
#         self.delay = delay
#     def run(self):
#         print ("开始线程：" + self.name)
#         print_time(self.name,self.delay)
#         print ("退出线程：" + self.name,k)
#
# def print_time(threadName,delay):
#     pyredis=Redis(host='127.0.0.1',port=6379,db=0)
#     p=pyredis.pipeline(transaction=True)
#     try:
#         p.watch('shop')
#         pi=int(p.get('shop'))
#         print('-'*20,pi)
#         if delay<=pi:
#             p.multi()
#             p.set('shop',pi-delay)
#             p.execute()
#             k.append(threadName)
#             print(threadName,rds.get('shop'))
#     except redis.exceptions.WatchError:
#         pass
#     return
#
#
# # 创建新线程
# thread1 = myThread(1, "Thread-1", 2)
# thread2 = myThread(2, "Thread-2", 2)
#
# # 开启新线程
# thread1.start()
# thread2.start()
from scheduler_task.tasks import delorder
from utils.start_end_time import get_week_start_end_time

print(get_week_start_end_time())

delorder('fdd209df-d44c-4299-9841-19be1bc58c0a')