from typing import Final
from types import TracebackType
from pathlib import Path
import sys
import logging

from loguru import logger

LOGS_PATH: Final[Path] = Path.cwd() / "logs"

FILE_NAME: Final[str] = "log_{time:DD.MM.YY_HH.mm.ss.SSSSSS!UTC}.txt"
FORMAT: Final[str] = "[<level>{level}</level>] ({name}) {message}"
FILE_FORMAT: Final[str] = "<green>{time:DD.MM.YY HH:mm:ss!UTC}</green> " + FORMAT


class InterceptHandler(logging.Handler):
    """ From logging to loguru """

    def emit(self, record):
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        depth = 6
        frame = sys._getframe(depth)
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _handle_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType
) -> None:
    exc_info = (exc_type, exc_value, exc_traceback)
    if not issubclass(exc_type, KeyboardInterrupt):
        error_logger.opt(exception=exc_info).error("Uncaught exception")
    return sys.__excepthook__(exc_type, exc_value, exc_traceback)


def configure(
    debug_files: bool = False,
    history_length: int = 10,
    show_vars: bool = False,
    **kwargs
):
    global error_logger

    LOGS_PATH.mkdir(exist_ok=True)
    logger.remove()
    logger.add(
        sink=sys.stdout,
        level="INFO",
        format=FORMAT,
        diagnose=show_vars,
        **kwargs
    )
    logger.add(
        sink=LOGS_PATH / FILE_NAME,
        level="INFO",
        format=FILE_FORMAT,
        retention=history_length,
        diagnose=show_vars,
        **kwargs
    )
    if debug_files:
        logger.add(
            sink=LOGS_PATH / f"debug_{FILE_NAME}",
            level="DEBUG",
            format=FILE_FORMAT,
            retention=history_length,
            diagnose=show_vars,
            **kwargs
        )

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
        datefmt="%d.%m.%y %H:%M:%S",
        handlers=(InterceptHandler(), ),
        level=0,
        force=True
    )

    error_logger = logger.bind(name="errors")  # FIXME: doesn't changes {name} in format
    sys.excepthook = _handle_exception
