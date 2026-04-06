#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

import click

from src.base.job_base import JobBase
from src.common.context import Context
from src.core.loader import Loader
from src.core.logger import Logger, LogLevel
from src.util import util


def _parse_job_name(name: str) -> tuple[str, str]:
    if "." not in name:
        raise click.ClickException(
            "Invalid job name format. Expected 'module_path.class_name', e.g. 'jobs.demo_job.DemoJob'."
        )
    module_path, class_name = name.rsplit(".", 1)
    if not module_path or not class_name:
        raise click.ClickException(
            "Invalid job name format. Expected 'module_path.class_name', e.g. 'jobs.demo_job.DemoJob'."
        )
    return module_path, class_name


def _build_job_arguments(arguments: tuple[str, ...]) -> Context:
    return JobBase.build_context_from_cli(arguments)


def _load_job_class(name: str, python_paths: tuple[str, ...] = ()):
    module_path, class_name = _parse_job_name(name)
    data_path = Path(__file__).resolve().parents[1] / "data"

    loader = Loader()
    for item in reversed(python_paths):
        loader.add_path(Path(item), index=0)
    loader.add_path(data_path, index=0)

    try:
        job_cls = loader.get_class(module_path, class_name)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(f"Failed to load job '{name}': {exc}") from exc

    if not isinstance(job_cls, type):
        raise click.ClickException(f"'{name}' is not a class.")
    if not issubclass(job_cls, JobBase):
        raise click.ClickException(f"'{name}' must inherit from JobBase.")
    return job_cls


def _build_job_instance(job_cls, arguments: tuple[str, ...]) -> JobBase:
    job_arguments = _build_job_arguments(arguments)
    try:
        return job_cls(arguments=job_arguments)
    except TypeError:
        # Compatibility path for subclasses using positional constructor style.
        return job_cls(job_arguments)


@click.command()
@click.option("-l", "--log", type=click.Path(file_okay=False), multiple=True, default=['_stderr'], help="log file list", metavar="log")
@click.option("--log-level", type=click.Choice(LogLevel.keys()), default="DEBUG", help="Set the logging level.", metavar="log-level")
@click.option("--python-path", type=click.Path(file_okay=False), multiple=True, default=(), help="Extra python import paths.", metavar="python-path")
@click.argument("name", required=True, type=click.STRING, metavar="name")
@click.argument("arguments", nargs=-1, metavar="arguments")
def main(log, log_level, python_path, name, arguments):
    util.setup_loggers(Logger(), log, log_level)

    logger = Logger().get_logger(__name__)

    logger.info(f"starting job: name={name}, args={arguments}")

    try:
        job_cls = _load_job_class(name, python_paths=tuple(python_path))
        job = _build_job_instance(job_cls, arguments)
        job.setup()
        result = job.exec()
        logger.info(f"job finished: {name}, result={result}")
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error(f"job failed: {name}, error={exc!r}")
        util.print_with_traceback(exc, printer=logger.error)
        raise click.ClickException(f"Job '{name}' execution failed: {exc}") from exc


if __name__ == "__main__":
    main()
