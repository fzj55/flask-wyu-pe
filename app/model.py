"""模型"""
import datetime

from sqlalchemy import or_

from exts import db, cache
from utils.start_end_time import get_week_start_end_time, get_day_start_end_time


class User(db.Model):
    """用户"""
    __tablename__ = 'user'

    id = db.Column(db.String(64), primary_key=True, nullable=False, unique=True, comment='id')
    name = db.Column(db.String(16), nullable=False, unique=True, comment='用户名')
    password = db.Column(db.String(128), nullable=False, comment='密码')
    # is_blacklist = db.Column(db.Boolean, default=False, nullable=False,comment='是否在黑名单')
    img = db.Column(db.String(128), comment='用户头像路径')
    reset_time = db.Column(db.DateTime, nullable=True, comment='重置时间')
    authority_id = db.Column(db.String(64), nullable=False, comment='权限id')

    @property
    def authority(self):
        """获取权限对象"""
        if not hasattr(self, '_authority'):
            self._authority = Authority.get(id=self.authority_id)
        return self._authority

    def orders(self):
        """用户的订单"""
        return Order.query.filter(Order.user_id == self.id).all()

    def delete(self):
        orders = self.orders()
        for order in orders:
            order.delete()
        db.session.delete(self)
        db.session.commit()
        cache.delete('Model:User:%s' % self.id)

    def get_residue_degree(self, place_id):
        place = Place.get(place_id)
        if place.parent_id != '-1':
            return -1

        weekstart, weekend = get_week_start_end_time()
        orders = Order.query.filter(Order.user_id == self.id, Order.create_time >= weekstart,
                                    Order.create_time <= weekend, or_(Order.status == 1, Order.status == 4)).all()

        already = 0
        for order in orders:
            t = TimeTable.get(order.timetable_id)
            if not t:
                continue
            check_place = Place.get(t.place_id)
            if check_place.parent_id != '-1':
                check_place = Place.get(check_place.parent_id)
            if place.id == check_place.id:
                already += 1
            if already >= place.book_frequency:
                return 0

        return place.book_frequency - already

    def is_reserved(self, drawtime_id):
        orders = Order.query.filter(Order.user_id == self.id, or_(Order.status == 1, Order.status == 4)).all()
        for old_order in orders:
            t = TimeTable.get(old_order.timetable_id)
            if t.drawtime_id == drawtime_id:
                return True
        return False


class Place(db.Model):
    """活动场所"""
    __tablename__ = 'place'

    id = db.Column(db.String(64), primary_key=True, nullable=False, unique=True, comment='id')
    name = db.Column(db.String(16), nullable=False, unique=True, index=True, comment='场所名称')
    is_open = db.Column(db.Boolean, nullable=False, index=True, comment='是否开放')
    book_frequency = db.Column(db.Integer, nullable=False, comment='可预约次数')
    img = db.Column(db.String(128), comment='场所图标路径')
    parent_id = db.Column(db.String(64), default=-1, nullable=False, index=True, comment='子场所')

    @property
    def parent(self):
        """获取父场所对象"""
        if not hasattr(self, '_parent'):
            self._parent = Place.get(id=self.parent_id)
        return self._parent

    def children(self):
        """获取所有子场所"""
        return self.__class__.query.filter(self.__class__.parent_id == self.id).all()

    def timetables(self):
        """获取场所的时间表"""
        return TimeTable.query.filter(TimeTable.place_id == self.id).all()

    def filter_timetables(self):
        """获取当前抽签对应的时间表"""
        now = datetime.datetime.now()
        drawtime = DrawTime.query.filter(DrawTime.place_id == self.id, DrawTime.draw_start_time <= now,
                                         DrawTime.draw_end_time >= now).first()
        return TimeTable.query.filter(TimeTable.place_id == self.id, TimeTable.drawtime_id == drawtime.id).order_by(
            TimeTable.start_time).all()

    def notice(self):
        """获取场所所有的有关公告"""
        return Notice.query.filter(Notice.place_id == self.id).all()

    def to_detail_dict(self, drawtime_id):
        data = self.to_dict()
        data['timetable'] = []
        time_set = set()

        timetables = TimeTable.query.filter(TimeTable.place_id == self.id,
                                            TimeTable.drawtime_id == drawtime_id).order_by(TimeTable.start_time).all()
        for timetable in timetables:
            date = timetable.start_time.strftime("%Y-%m-%d")
            time = '-'.join([timetable.start_time.strftime("%H:%M"), timetable.end_time.strftime("%H:%M")])
            time = ' '.join([date, time])
            time_set.add(time)
            timetable_data = timetable.to_dict(0, True, 'cycle_time', 'initial_ticket_num')
            timetable_data['time'] = time
            data['timetable'].append(timetable_data)
        return data, time_set


class TimeTable(db.Model):
    """时间表"""
    __tablename__ = 'timetable'

    id = db.Column(db.String(64), primary_key=True, nullable=False, unique=True, comment='id')
    # draw_start_time = db.Column(db.DateTime, nullable=False, comment='开始进入抽签时间')
    # draw_end_time = db.Column(db.DateTime, nullable=False, comment='结束进入抽签时间')
    # book_start_time = db.Column(db.DateTime, nullable=False, comment='开始进入抽奖时间')
    # book_end_time = db.Column(db.DateTime, nullable=False, comment='结束进入抽奖时间')
    start_time = db.Column(db.DateTime, nullable=False, comment='开始时间')
    end_time = db.Column(db.DateTime, nullable=False, comment='结束时间')
    ticket_num = db.Column(db.Integer, nullable=False, comment='票数')
    # can_book_many=db.Column(db.Boolean,nullable=False,comment='是否可以预定多次')
    can_book_num = db.Column(db.Integer, nullable=False, comment='可容纳人数')
    # cycle_time = db.Column(db.String(64), nullable=True, comment='循环时间')
    initial_ticket_num = db.Column(db.Integer, nullable=False, comment='初始票数')
    is_follow_cycle = db.Column(db.Boolean, nullable=False, comment='是否跟随循环')

    place_id = db.Column(db.String(64), nullable=False, comment='关联场所id')
    drawtime_id = db.Column(db.String(64), nullable=False, comment='关联抽签表id')

    @property
    def place(self):
        """获取所属场所对象"""
        if not hasattr(self, '_place'):
            self._place = Authority.get(id=self.place_id)
        return self._place

    @property
    def drawtime(self):
        """获取所属场所对象"""
        if not hasattr(self, '_drawtime'):
            self._drawtime = DrawTime.get(id=self.drawtime_id)
        return self._drawtime

    def orders(self):
        """获取该时间段的所有订单"""
        return Order.query.filter(Order.timetable_id == self.id).all()

    def success_orders(self):
        """获取该时间段的预定成功的订单"""
        return Order.query.filter(Order.timetable_id == self.id,or_(Order.status==1,Order.status==4)).all()

    def delete(self):
        """订单与时间表解绑"""
        orders = Order.query.filter(Order.timetable_id == self.id).all()
        for order in orders:
            if order.status == 2:
                order.timetable_id = None
                db.session.add(order)
            elif order.status == 1:
                order.timetable_id = None
                order.status = 0
                db.session.add(order)
            else:
                order.delete()
        db.session.delete(self)
        db.session.commit()
        cache.delete('Model:TimeTable:%s' % self.id)

    def remove(self):
        """物理删除关联订单"""
        orders = Order.query.filter(Order.timetable_id == self.id).all()
        for order in orders:
            order.delete()
        db.session.delete(self)
        db.session.commit()
        cache.delete('Model:TimeTable:%s' % self.id)


class DrawTime(db.Model):
    """抽签时间表"""
    __tablename__ = 'drawtime'

    id = db.Column(db.String(64), primary_key=True, nullable=False, unique=True, comment='id')
    draw_start_time = db.Column(db.DateTime, nullable=False, comment='开始进入抽签时间')
    draw_end_time = db.Column(db.DateTime, nullable=False, comment='结束进入抽签时间')
    book_start_time = db.Column(db.DateTime, nullable=False, comment='开始进入抽奖时间')
    book_end_time = db.Column(db.DateTime, nullable=False, comment='结束进入抽奖时间')
    cycle_time = db.Column(db.String(64), nullable=True, comment='循环时间')
    place_id = db.Column(db.String(64), nullable=False, comment='关联场所id')

    @property
    def place(self):
        """获取关联场地对象"""
        if not hasattr(self, '_place'):
            self._place = Place.get(id=self.place_id)
        return self._place

    def timetables(self):
        return TimeTable.query.filter(TimeTable.drawtime_id == self.id).all()

    def delete(self):
        orders = Order.query.filter(Order.drawtime_id == self.id).all()
        for order in orders:
            order.delete()
        timetables = TimeTable.query.filter(TimeTable.drawtime_id == self.id).all()
        for timetable in timetables:
            timetable.remove()
        db.session.delete(self)
        db.session.commit()
        cache.delete('Model:DrawTime:%s' % self.id)

    @classmethod
    def get_today(cls, place_id):
        date = datetime.date.today()
        drawtime = DrawTime.query.filter(DrawTime.place_id == place_id, DrawTime.draw_start_time >= date,
                                         DrawTime.draw_end_time <= date + datetime.timedelta(days=1)).first()
        return drawtime

    @classmethod
    def get_yesterday(cls, place_id):
        date = datetime.date.today()
        drawtime = DrawTime.query.filter(DrawTime.place_id == place_id,
                                         DrawTime.draw_start_time >= date - datetime.timedelta(days=1),
                                         DrawTime.draw_end_time <= date).first()
        return drawtime

    def to_detail_dict(self):
        data = self.to_dict(0, False, 'place_id')
        data['place'] = self.place.to_dict()
        return data


class Order(db.Model):
    """活动，预约订单"""
    __tablename__ = 'order'

    id = db.Column(db.String(64), primary_key=True, nullable=False, unique=True, comment='id')
    user_id = db.Column(db.String(64), nullable=False, comment='用户id')
    timetable_id = db.Column(db.String(64), comment='时间表id')
    drawtime_id = db.Column(db.String(64), comment='时间表id')
    create_time = db.Column(db.DateTime, nullable=False, comment='订单创建时间')
    book_num = db.Column(db.Integer, nullable=False, comment='订单人数')
    status = db.Column(db.Integer, nullable=False, default=0, comment='订单状态')
    parent_order_id = db.Column(db.String(64), comment='父订单')

    @property
    def user(self):
        """获取预约用户对象"""
        if not hasattr(self, '_user'):
            self._user = User.get(id=self.user_id)
        return self._user

    @property
    def timetable(self):
        """获取预约时间表对象"""
        if not hasattr(self, '_timetable'):
            self._timetable = TimeTable.get(id=self.timetable_id)
        return self._timetable

    @property
    def drawtime(self):
        """获取预约时间表对象"""
        if not hasattr(self, '_drawtime'):
            self._drawtime = DrawTime.get(id=self.drawtime_id)
        return self._drawtime

    def delete(self):
        if self.timetable_id:
            timetable = TimeTable.query.get(self.timetable_id)
            timetable.ticket_num += self.book_num
            db.session.add(timetable)
        db.session.delete(self)
        db.session.commit()
        cache.delete('Model:Order:%s' % self.id)

    def to_detail_dict(self):
        data = {}
        data['order_id'] = self.id
        data['book_num'] = self.book_num
        data['create_time'] = self.create_time.strftime('%Y-%m-%d %H:%M:%S')
        data['status'] = self.status
        data['parent_oder_id'] = self.parent_order_id
        data['timetable'] = {}
        data['place'] = {}
        data['drawtime'] = {}
        drawtime = DrawTime.get(self.drawtime_id)
        data['drawtime']['draw_id'] = drawtime.id
        data['drawtime']['draw_start_time'] = drawtime.draw_start_time.strftime('%Y-%m-%d %H:%M:%S')
        data['drawtime']['draw_end_time'] = drawtime.draw_end_time.strftime('%Y-%m-%d %H:%M:%S')
        if self.timetable_id and (self.status == 1 or self.status == 4):
            timetable = TimeTable.get(self.timetable_id)
            data['timetable']['timetable_id'] = timetable.place_id
            data['timetable']['book_start_time'] = drawtime.book_start_time.strftime('%Y-%m-%d %H:%M:%S')
            data['timetable']['book_end_time'] = drawtime.book_end_time.strftime('%Y-%m-%d %H:%M:%S')
            data['timetable']['start_time'] = timetable.start_time.strftime('%Y-%m-%d %H:%M:%S')
            data['timetable']['end_time'] = timetable.end_time.strftime('%Y-%m-%d %H:%M:%S')
            place = Place.get(timetable.place_id)
            data['place']['name'] = place.name
            data['place']['place_id'] = place.parent_id
        else:
            place = Place.get(drawtime.place_id)
            data['place']['name'] = place.name
            data['place']['place_id'] = place.id
            data['place']['parent_id'] = place.parent_id
        return data


class Authority(db.Model):
    """权限"""
    __tablename__ = 'authority'

    id = db.Column(db.String(64), primary_key=True, nullable=False, unique=True, comment='id')
    name = db.Column(db.String(16), nullable=False, unique=True, index=True, comment='权限名称')

    def users(self):
        """获取用该权限的用户"""
        return User.query.filter(User.authority_id == self.id).all()


class Notice(db.Model):
    """公告"""
    __tablename__ = 'notice'

    id = db.Column(db.String(64), primary_key=True, nullable=False, unique=True, comment='id')
    title = db.Column(db.String(64), nullable=False, comment='标题')
    content = db.Column(db.TEXT, nullable=False, comment='内容')
    is_urgent = db.Column(db.Boolean, default=False,nullable=False,index=True,comment='是否为紧急公告')
    create_time = db.Column(db.DateTime, nullable=False, comment='订单创建时间')
    place_id = db.Column(db.String(64), comment='所属场馆id')

    @property
    def place(self):
        """获取公告所属的场所对象"""
        if not hasattr(self, '_place'):
            self._place = Place.get(id=self.place_id)
        return self._place
