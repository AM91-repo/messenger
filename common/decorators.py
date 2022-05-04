import logging
import sys
import traceback

from common.config import LOGGER_CLIENT, LOGGER_SERVER

if sys.argv[0] == 'server.py':
    LOGGER = logging.getLogger(LOGGER_SERVER)
else:
    LOGGER = logging.getLogger(LOGGER_CLIENT)


def func():
    print(
        f'Calling from a function {traceback.format_stack()}. ')


def log(func):
    def wraper(*args, **kwargs):
        ret = func(*args, **kwargs)
        LOGGER.debug(f'Function: {func.__name__}(). '
                     f'Module: {func.__module__}. '
                     f'Calling from a function {traceback.format_stack()[0].strip().split()[-1]}. ')
        return ret
    return wraper


if __name__ == '__main__':
    func()
