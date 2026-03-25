# -*- coding:utf-8 -*-

"""
Base Job Component
"""
import abc
from typing import Optional

from src.common.context import SerializableContext, Context


class JobBase(object, metaclass=abc.ABCMeta):
    def __init__(self, arguments: Optional[Context]=None):
        if arguments is None:
            arguments = {}
        self.config = SerializableContext({})
        self.arguments = self._parse_arguments(arguments)
        self.setup()


    def _parse_arguments(self, arguments: Context) -> Context:
        ...

    @abc.abstractmethod
    def _setup(self):
        ...

    @abc.abstractmethod
    def _exec(self):
        ...

    @abc.abstractmethod
    def _submit(self):
        ...

    @abc.abstractmethod
    def _recovery(self):
        ...
