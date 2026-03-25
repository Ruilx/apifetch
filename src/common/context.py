# -*- coding: utf-8 -*-
import ujson
from typing import Any

from src.common.types import SerializableType


class Context(object):
    def __init__(self, storage: dict[str, Any]):
        self._storage = storage

    def get(self, name: str, default: Any | None = None) -> Any:
        return self._storage.get(name, default)

    def __getitem__(self, name: str) -> Any:
        return self._storage.get(name)

    def set(self, name: str, value: Any) -> None:
        self._storage[name] = value

    def __setitem__(self, name: str, value: Any) -> None:
        self.set(name, value)

    def __delitem__(self, name: str):
        del self._storage[name]

    def __contains__(self, name: str):
        return name in self._storage

    def _dump(self):
        return self._storage


class SerializableContext(Context):
    def __init__(self, storage: dict[str, SerializableType]):
        super().__init__(storage)

    def get(self, name: str, default: SerializableType | None = None) -> SerializableType:
        return super().get(name, default)

    def set(self, name: str, value: SerializableType) -> None:
        self._storage[name] = value

    def __setitem__(self, name: str, value: SerializableType) -> None:
        self.set(name, value)

    def __getstate__(self):
        return ujson.dumps(self._storage, ensure_ascii=False, indent=0)

    def __setstate__(self, state):
        self._storage = ujson.loads(state)
