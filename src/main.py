#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click

from src.core.logger import Logger, LogLevel
from src.util import util


@click.command()
@click.option("-l", "--log", type=click.Path(file_okay=False), multiple=True, default=['_stderr'], help="log file list")
@click.option("--log-level", type=click.Choice(LogLevel.keys()), default="DEBUG", help="Set the logging level.")
def main(log, log_level):
    util.setup_loggers(Logger(), log, log_level)

    logger = Logger().get_logger(__name__)

    logger.info("Hello, world!")


if __name__ == "__main__":
    main()
