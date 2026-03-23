# -*- coding: utf-8 -*-

from functools import wraps
from threading import Lock

"""
Singleton单例模式使用装饰器模式从外部控制方案形成单例模式，任何位置使用装饰的对象，都指向这一个唯一的对象
注意：一般不要给单例模式的构造函数参数，因为你根本不知道是不是在你该构造的时候构造出来了。如果不是第一次构造出的对象，那么将会忽略从第二次传入的任何一个参数。
"""


def singleton(cls):
    instance = {}
    lock = Lock()

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instance:
            with lock:
                if cls not in instance:
                    instance[cls] = cls(*args, **kwargs)
        return instance[cls]

    return get_instance
