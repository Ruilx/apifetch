# -*- coding: utf-8 -*-

"""Minimal plugin example for lazy loading validation."""

from src.base.plugin_base import PluginBase


class EchoPlugin(PluginBase):
    def _setup(self):
        self._history: list[str] = []

    def _teardown(self):
        self._history.clear()

    def echo(self, message: str) -> str:
        if not isinstance(message, str) or len(message) == 0:
            raise ValueError("message must be non-empty string")
        self._history.append(message)
        return message

    def history(self) -> list[str]:
        return list(self._history)

    def recover(self, exc: BaseException):
        # Keep plugin in a clean state after call failures.
        self._history = []
