# -*- coding: utf-8 -*-

import os
import time
import datetime

from typing import Callable

from src.core.logger import Logger, LogLevel, LogLevelType, LogPathType


def print_with_traceback(e: BaseException, printer: Callable = print):
    import traceback
    printer(f"{e.__class__.__name__}: {e!r}")
    for line in traceback.format_tb(e.__traceback__):
        printer(line.rstrip())

def timestamp():
    return int(time.time())

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def machine_cpu_count():
    return os.cpu_count() or 1

def setup_loggers(logger: Logger, logs: tuple[LogPathType], log_level: LogLevelType):
    for log in logs:
        logger.set_level(log_level)
        logger.add_stream(log)
