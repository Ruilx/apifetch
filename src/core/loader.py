# -*- coding: utf-8 -*-

import importlib
import os
import pathlib
import sys

from src.base.singleton import singleton


@singleton
class Loader(object):
    def __init__(self):
        ...

    def add_path(self, path: os.PathLike[str] | pathlib.Path, index: int = -1):
        if not os.path.exists(path):
            raise FileNotFoundError
        if index == -1:
            sys.path.append(path.resolve().__str__())
        else:
            sys.path.insert(index, path.resolve().__str__())


    def get_class(self, module_path: str, class_name: str):
        assert module_path.__len__() > 0, "module_path is empty"
        assert class_name.__len__() > 0, "class_name is empty"
        return getattr(importlib.import_module(module_path), class_name)
