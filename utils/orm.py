import datetime

from exts import db, cache


def to_dict(self,date_time=0,is_array=False, *ignore_fileds):
    '''将一个模型转换成一个dict'''
    attr_dict = {}
    for key,value in dict(self.__dict__).items():  # 遍历所有字段
        if dict(self.__class__.__dict__).get(key,None):
            if key not in ignore_fileds:
                if isinstance(value,datetime.datetime):
                    if date_time==0:
                        value=value.strftime('%Y-%m-%d %H:%M:%S')
                    elif date_time==1:
                        value = value.strftime('%Y-%m-%d')
                    else:
                        value = value.strftime('%H:%M:%S')
                if key=='can_book_num' and is_array:
                    value=[i for i in range(1,value+1)]
                attr_dict[key]=value
    return attr_dict

def get(cls,id):
    '''数据优先从缓存获取，缓存取不到再从数据库获取'''
    #从缓存获取
    key = 'Model:%s:%s' % (cls.__name__, id)
    model_obj = cache.get(key)
    if isinstance(model_obj, cls):
        return model_obj

    #缓存里没有，直接从数据库获取，同时写入缓存
    model_obj =cls.query.get(id)

    if model_obj:
        #写入缓存，并且缓存一周
        key = 'Model:%s:%s'% (cls.__name__, model_obj.id)
        cache.set(key, model_obj,604800) #缓存一周
    return model_obj

def add_with_cache(model_save_func):
    def add(self):
        '''存入数据库后，同时写入缓存'''
        #调用生的 db.session.add将数据保存到数据库
        model_save_func(self)
        #添加缓存
        key = 'Model:%s:%s' % (self.__class__.__name__, self.id)
        cache.set(key, self,604800)
    return add

#猴子补丁
def patch_model():
    '''
    动态更新 Model 方法
    Model在Django中是一个特殊的类，如果通过继承的方式来增加或修改原有方法，Django会将
    继承的类识别为一个普通的app.model,所以只能通过 monkey patch（猴子补丁）(就是此方法)的方式动态修改
    '''
    #动态添加类方法 get,get_or_create
    db.Model.get = classmethod(get)
    #修改save
    db.session.add = add_with_cache(db.session.add)
    #添加 to_dict
    db.Model.to_dict = to_dict
