import logging
import socket
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


def login_required(func):
    """
    A decorator that verifies that the client is authorized on the server.
    Checks that the transmitted socket object is in
    the list of authorized clients.
    Except for the transfer of the dictionary-
    authorization request. If the client is not logged in,
    generates a TypeError exception
    """

    def checker(*args, **kwargs):
        from server.core import MessageProcessor
        from common.config import ACTION, ACTION_PRESENCE
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == ACTION_PRESENCE:
                        found = True
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker



if __name__ == '__main__':
    func()
