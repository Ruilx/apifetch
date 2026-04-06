# -*- coding:utf-8 -*-

"""Base plugin abstraction for reusable tools (db, notifier, etc.)."""

import abc
from typing import Any, Mapping

from src.common.context import Context


class PluginBase(object, metaclass=abc.ABCMeta):
	def __init__(self, name: str, config: Mapping[str, Any] | Context | None = None):
		self.name = name
		if config is None:
			self.config = Context({})
		elif isinstance(config, Context):
			self.config = config
		elif isinstance(config, Mapping):
			self.config = Context(dict(config))
		else:
			raise TypeError(f"Unsupported plugin config type: {type(config)!r}")

		self._is_setup = False

	def setup(self):
		if self._is_setup:
			return
		self._setup()
		self._is_setup = True

	def teardown(self):
		if not self._is_setup:
			return
		self._teardown()
		self._is_setup = False

	@abc.abstractmethod
	def _setup(self):
		...

	@abc.abstractmethod
	def _teardown(self):
		...

	def recover(self, exc: BaseException):
		"""Recover plugin internal resources after runtime failure."""
		...

	def healthcheck(self) -> bool:
		return True
