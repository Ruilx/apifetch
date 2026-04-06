# -*- coding:utf-8 -*-

"""Plugin manager with lazy-loading support."""

from __future__ import annotations

import dataclasses
from typing import Any, Callable

from src.base.plugin_base import PluginBase
from src.core.loader import Loader


class PluginError(RuntimeError):
    pass


class PluginRegistrationError(PluginError):
    pass


class PluginLoadError(PluginError):
    pass


class PluginRuntimeError(PluginError):
    pass


@dataclasses.dataclass
class _PluginEntry:
    factory: Callable[[], PluginBase]
    lazy: bool = True
    auto_setup: bool = True
    instance: PluginBase | None = None


class PluginManager(object):
    def __init__(self):
        self._entries: dict[str, _PluginEntry] = {}

    def register_instance(self, name: str, plugin: PluginBase, auto_setup: bool = False) -> PluginBase:
        if name in self._entries:
            raise PluginRegistrationError(f"Plugin '{name}' is already registered")
        if not isinstance(plugin, PluginBase):
            raise PluginRegistrationError(f"Plugin '{name}' must inherit from PluginBase")

        self._entries[name] = _PluginEntry(
            factory=lambda: plugin,
            lazy=False,
            auto_setup=auto_setup,
            instance=plugin,
        )
        if auto_setup:
            plugin.setup()
        return plugin

    def register_factory(
        self,
        name: str,
        factory: Callable[[], PluginBase],
        lazy: bool = True,
        auto_setup: bool = True,
    ):
        if name in self._entries:
            raise PluginRegistrationError(f"Plugin '{name}' is already registered")
        self._entries[name] = _PluginEntry(factory=factory, lazy=lazy, auto_setup=auto_setup)
        if not lazy:
            self._build_instance(name)
        return name

    def register_class(
        self,
        name: str,
        module_path: str,
        class_name: str,
        *args,
        lazy: bool = True,
        auto_setup: bool = True,
        **kwargs,
    ):
        def _factory() -> PluginBase:
            plugin_cls = Loader().get_class(module_path, class_name)
            plugin = plugin_cls(*args, **kwargs)
            if not isinstance(plugin, PluginBase):
                raise PluginLoadError(f"'{module_path}.{class_name}' is not a PluginBase implementation")
            return plugin

        return self.register_factory(name, _factory, lazy=lazy, auto_setup=auto_setup)

    def has(self, name: str) -> bool:
        return name in self._entries

    def get(self, name: str, setup: bool = True) -> PluginBase:
        entry = self._entries.get(name)
        if entry is None:
            raise PluginLoadError(f"Plugin '{name}' is not registered")

        plugin = self._build_instance(name)
        if setup and entry.auto_setup:
            plugin.setup()
        return plugin

    def setup_all(self):
        for name in self._entries:
            self.get(name, setup=True)

    def teardown_all(self, ignore_errors: bool = True):
        errors: list[BaseException] = []
        for entry in self._entries.values():
            if entry.instance is None:
                continue
            try:
                entry.instance.teardown()
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)
                if not ignore_errors:
                    raise
        return errors

    def recover(self, name: str, exc: BaseException):
        plugin = self.get(name, setup=False)
        try:
            plugin.recover(exc)
        except Exception as recover_exc:  # noqa: BLE001
            raise PluginRuntimeError(f"Plugin '{name}' recover failed: {recover_exc}") from recover_exc

    def call(self, name: str, method_name: str, *args, **kwargs):
        plugin = self.get(name, setup=True)
        if not hasattr(plugin, method_name):
            raise PluginRuntimeError(f"Plugin '{name}' has no method '{method_name}'")

        method = getattr(plugin, method_name)
        if not callable(method):
            raise PluginRuntimeError(f"Plugin '{name}.{method_name}' is not callable")

        try:
            return method(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            try:
                plugin.recover(exc)
            except Exception:
                pass
            raise PluginRuntimeError(f"Plugin '{name}.{method_name}' failed: {exc}") from exc

    def _build_instance(self, name: str) -> PluginBase:
        entry = self._entries.get(name)
        if entry is None:
            raise PluginLoadError(f"Plugin '{name}' is not registered")

        if entry.instance is not None:
            return entry.instance

        try:
            plugin = entry.factory()
        except Exception as exc:  # noqa: BLE001
            raise PluginLoadError(f"Plugin '{name}' factory failed: {exc}") from exc

        if not isinstance(plugin, PluginBase):
            raise PluginLoadError(f"Plugin '{name}' factory must return PluginBase")

        entry.instance = plugin
        return plugin
