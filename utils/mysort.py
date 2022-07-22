import re

from app.model import Place


def name_sort(name):
    return int(re.findall('\d+', name)[0])