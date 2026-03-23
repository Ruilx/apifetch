# -*- coding: utf-8 -*-

import abc

from src.core.component import Component


class ComponentHub(metaclass=abc.ABCMeta):
    def __init__(self):
        self.components = {}

    def has(self, name: str):
        return name in self.components

    def set(self, name: str, component: Component):
        if not self.has(name):
            self.components[name] = component
            return
        raise ValueError(f"Component name '{name}' already set in ComponentHub")

    def get(self, name: str):
        if not self.has(name):
            raise ValueError(f"Component name '{name}' not found instance, maybe this component method is not supported.")
        component = self.components[name]
        assert isinstance(component, Component)
        cls = component.get_instance()
        self._check_component(cls)
        return cls

    @abc.abstractmethod
    def _check_component(self, cls):
        raise NotImplementedError()
