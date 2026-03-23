# -*- coding: utf-8 -*-

import logging
import os
import sys
from typing import Literal, Union

from src.base.singleton import singleton

LogLevel = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
}

LogLevelType = Literal["DEBUG", "INFO", "WARNING", "ERROR"]
LogPathType = Union[os.PathLike, Literal["_stderr"], Literal["_stdout"]]

LogFormatter = "[%(asctime)s] %(levelname)s(%(process)d@%(threadName)s): %(filename)s:%(lineno)s: %(name)s: %(message)s"

@singleton
class Logger(object):
    def __init__(self):
        self.loggers = {}
        self.level: LogLevelType = "DEBUG"
        self.streams = set()

    def set_level(self, level):
        assert level in LogLevel, f"Log level '{level}' is not supported."
        self.level = level

    def get_level(self):
        return self.level

    def add_stream(self, stream: LogPathType):
        self.streams.add(stream)

    def get_streams(self):
        return self.streams

    def add_logger(self, name: str, level: LogLevelType = "DEBUG"):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        self._setup(logger)
        self.loggers[name] = logger

    def get_logger(self, name: str):
        if name not in self.loggers:
            self.add_logger(name, self.level)
        return logging.getLogger(name)

    def _setup(self, logger):
        formatter = logging.Formatter(LogFormatter)
        if len(self.streams) < 1:
            print("Program has no logging stream, no logs will output.", file=sys.stderr)
            print("Note: Please use '--log=_stderr' log to the stderr.", file=sys.stderr)

        if '_stderr' in self.streams and '_stdout' in self.streams:
            print("There has stdout and stderr logging exist in log streams, only stderr output will affect.")
            self.streams.remove("-")

        for item in self.streams:
            assert isinstance(item, str), f"Every stream item needs string type, but '{type(item)}' found."
            if item == "_stdout":
                handler = logging.StreamHandler(stream=sys.stdout)
            elif item == "_stderr":
                handler = logging.StreamHandler(stream=sys.stderr)
            else:
                handler = logging.FileHandler(item, encoding="utf-8", delay=True)

            if handler is not None:
                handler.setFormatter(formatter)
                logger.handlers.append(handler)

    @staticmethod
    def global_logger():
        return Logger().get_logger("_")

def setup_loggers(logger: Logger, logs: list[LogPathType] | tuple[LogPathType] | Literal["_stderr", "_stdout"], level_str: str = 'DEBUG'):
    logger.set_level(level_str)
    if isinstance(logs, (list, tuple)):
        for log in logs:
            logger.add_stream(log)
    else:
        logger.add_stream(logs)
