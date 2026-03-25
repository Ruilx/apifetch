# -*- coding: utf-8 -*-
from typing import Union

SerializableType = Union[str, bool, int, float, complex, dict[str, ...], list[...], tuple[...], None]

StructType = Union[SerializableType, set[...]]

NumberType = Union[int, float, complex]

ContainerType = Union[list, tuple, set]
