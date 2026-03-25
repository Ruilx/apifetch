#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click

from src.core.logger import Logger, LogLevel
from src.util import util


@click.command()
@click.option("-l", "--log", type=click.Path(file_okay=False), multiple=True, default=['_stderr'], help="log file list", metavar="log")
@click.option("--log-level", type=click.Choice(LogLevel.keys()), default="DEBUG", help="Set the logging level.", metavar="log-level")
@click.argument("name", required=True, type=click.STRING, metavar="name")
@click.argument("arguments", nargs=-1, metavar="arguments")
def main(log, log_level, name, arguments):
    util.setup_loggers(Logger(), log, log_level)

    logger = Logger().get_logger(__name__)

    logger.info("Hello, world!")

    logger.info(f"job name is :{name}, args={arguments}")


if __name__ == "__main__":
    main()
