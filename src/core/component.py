# -*- coding:utf-8 -*-
from src.core.loader import Loader


class Component(object):
    def __init__(self, name: str, module_path: str, class_name: str):
        self.name = name
        self.module_path = module_path
        self.class_name = class_name
        self.instance = None

    def get_instance(self):
        if not self.instance:
            assert self.module_path, "module_path is empty"
            assert self.class_name, "class_path is empty"
            self.instance = Loader().get_class(self.module_path, self.class_name)
        return self.instance

    def get_module_path(self):
        return self.module_path

    def get_class_name(self):
        return self.class_name

    def clear_instance(self):
        _class = self.instance.__class__
        del self.instance
        self.instance = None
        if _class.__name__ in globals():
            del globals()[_class.__name__]
