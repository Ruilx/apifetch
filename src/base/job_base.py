# -*- coding:utf-8 -*-

"""
Base Job Component
"""
import abc
import time
from typing import Any, Callable, Mapping, Optional, Sequence

from src.common.context import SerializableContext, Context
from src.base.plugin_base import PluginBase
from src.core.plugin_manager import PluginManager


class JobBase(object, metaclass=abc.ABCMeta):
    def __init__(
        self,
        arguments: Optional[Context | Mapping[str, Any]] = None,
        max_attempts: int = 1,
        initial_delay_seconds: float = 0.0,
        max_delay_seconds: float = 30.0,
        backoff_multiplier: float = 2.0,
        retry_window_seconds: float | None = None,
    ):
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if initial_delay_seconds < 0:
            raise ValueError("initial_delay_seconds must be >= 0")
        if max_delay_seconds < 0:
            raise ValueError("max_delay_seconds must be >= 0")
        if backoff_multiplier < 1:
            raise ValueError("backoff_multiplier must be >= 1")
        if retry_window_seconds is not None and retry_window_seconds < 0:
            raise ValueError("retry_window_seconds must be >= 0")

        self.config = SerializableContext({})
        self.arguments = self._parse_arguments(arguments)
        self._is_setup = False
        self._apis: dict[str, Any] = {}
        self.plugins = PluginManager()

        self.max_attempts = max_attempts
        self.initial_delay_seconds = initial_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.backoff_multiplier = backoff_multiplier
        self.retry_window_seconds = retry_window_seconds

        self.setup()

    def _parse_arguments(self, arguments: Optional[Context | Mapping[str, Any]]) -> Context:
        if arguments is None:
            return Context({})
        if isinstance(arguments, Context):
            return arguments
        if isinstance(arguments, Mapping):
            return Context(dict(arguments))
        raise TypeError(f"Unsupported arguments type: {type(arguments)!r}")

    @staticmethod
    def build_context_from_cli(arguments: Sequence[str]) -> Context:
        """Convert CLI args into Context with options/positional/raw fields."""
        options: dict[str, str | bool] = {}
        positional: list[str] = []
        for item in arguments:
            if item.startswith("--"):
                key_value = item[2:]
                if "=" in key_value:
                    key, value = key_value.split("=", 1)
                    options[key] = value
                else:
                    options[key_value] = True
            elif "=" in item:
                key, value = item.split("=", 1)
                options[key] = value
            else:
                positional.append(item)
        return Context({"options": options, "positional": positional, "raw": list(arguments)})

    def setup(self):
        if self._is_setup:
            return
        self._setup()
        self._is_setup = True

    def _pri_exec(self):
        ...

    def _post_exec(self, result: Any):
        ...

    @abc.abstractmethod
    def _setup(self):
        ...

    @abc.abstractmethod
    def _exec(self):
        ...

    @abc.abstractmethod
    def _submit(self, result: Any):
        ...

    @abc.abstractmethod
    def _recovery(self, exc: BaseException):
        ...

    def _is_retryable(self, exc: BaseException) -> bool:
        return True

    def _next_wait_seconds(self, attempt_index: int) -> float:
        delay = min(
            self.initial_delay_seconds * (self.backoff_multiplier ** attempt_index),
            self.max_delay_seconds,
        )
        return max(0.0, delay)

    def _can_retry_by_time_window(self, started_at: float, wait_seconds: float) -> bool:
        if self.retry_window_seconds is None:
            return True
        return (time.monotonic() - started_at + wait_seconds) <= self.retry_window_seconds

    def _before_retry(self, exc: BaseException, next_wait_seconds: float, next_attempt_no: int):
        ...

    def register_api(self, name: str, api_instance: Any):
        """Register a pre-built API instance for this job."""
        self._apis[name] = api_instance
        return api_instance

    def get_api(self, name: str):
        if name not in self._apis:
            raise KeyError(f"API '{name}' is not registered")
        return self._apis[name]

    def call_api(self, name: str):
        api = self.get_api(name)
        if not hasattr(api, "exec"):
            raise TypeError(f"API '{name}' has no exec() method")
        return api.exec()

    def register_plugin_instance(self, name: str, plugin_instance: PluginBase, auto_setup: bool = False):
        return self.plugins.register_instance(name, plugin_instance, auto_setup=auto_setup)

    def register_plugin_factory(
        self,
        name: str,
        factory: Callable[[], PluginBase],
        lazy: bool = True,
        auto_setup: bool = True,
    ):
        return self.plugins.register_factory(name, factory, lazy=lazy, auto_setup=auto_setup)

    def register_plugin_class(
        self,
        name: str,
        module_path: str,
        class_name: str,
        *args,
        lazy: bool = True,
        auto_setup: bool = True,
        **kwargs,
    ):
        return self.plugins.register_class(
            name,
            module_path,
            class_name,
            *args,
            lazy=lazy,
            auto_setup=auto_setup,
            **kwargs,
        )

    def get_plugin(self, name: str):
        return self.plugins.get(name)

    def call_plugin(self, name: str, method_name: str, *args, **kwargs):
        return self.plugins.call(name, method_name, *args, **kwargs)

    def exec(self):
        self.setup()
        started_at = time.monotonic()
        last_exception: BaseException | None = None
        try:
            for attempt in range(self.max_attempts):
                try:
                    self._pri_exec()
                    result = self._exec()
                    self._post_exec(result)
                    self._submit(result)
                    return result
                except Exception as exc:  # noqa: BLE001
                    last_exception = exc
                    self._recovery(exc)

                    if not self._is_retryable(exc):
                        raise

                    if attempt >= self.max_attempts - 1:
                        raise

                    wait_seconds = self._next_wait_seconds(attempt)
                    if not self._can_retry_by_time_window(started_at, wait_seconds):
                        raise

                    self._before_retry(exc, wait_seconds, attempt + 2)
                    time.sleep(wait_seconds)

            if last_exception is not None:
                raise last_exception
            raise RuntimeError("Unreachable job execution state")
        finally:
            self.plugins.teardown_all(ignore_errors=True)
