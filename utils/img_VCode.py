import datetime
import uuid
from random import randint, choice
from PIL import Image, ImageFont, ImageDraw, ImageFilter


#随机颜色产生
from flask import session

import settings


def get_random_color():
    return (randint(0,255),randint(0,255),randint(0,255))

#绘制验证码
def generate_image():
    size=(130,50)
    #创建画布
    im=Image.new('RGB',size,color=get_random_color())
    #创建字体
    font = ImageFont.truetype('./static/font/方正粗黑宋简体.ttf',size=40)
    #创建ImageDraw对象
    draw=ImageDraw.Draw(im)
    #绘制验证码
    code='1'
    # for i in range(4):
    #     a=chr(randint(65,90))
    #     b=str(randint(0,9))
    #     c=a+b
    #     d=choice(c)
    #     code+=d
    #     draw.text((5+randint(4,7)+25*i,1),text=d,fill=get_random_color(),font=font)
    #绘制干扰线
    for i in range(6):
        x1=randint(0,130)
        y1=randint(0,25)

        x2=randint(0,130)
        y2=randint(25,50)

        draw.line(((x1,y1),(x2,y2)),fill=get_random_color())
    #滤镜
    im=im.filter(ImageFilter.EDGE_ENHANCE)

    return im,code



def make_csrf_token():
    crsf_token = uuid.uuid5(uuid.NAMESPACE_DNS, str(datetime.datetime.now()))
    session['crsf_token'] = crsf_token
    return crsf_token