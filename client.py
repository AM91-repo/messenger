from email import message
import json
from multiprocessing.spawn import import_main_path
import sys
import socket
import logging
import logs.config_client_log
import common.jim as jim

from common.decorators import log
from common.config import (USER, ACCOUNT_NAME, RESPONSE, ERROR, MAX_CONNECTIONS,
                           LOGGER_CLIENT, DEFAULT_IP_ADDRESS, DEFAULT_PORT, USER_TEST)
from common.utils import send_message, get_message, create_parser

LOGGER = logging.getLogger(LOGGER_CLIENT)


def create_message(account_name):
    message = jim.PRESENCE
    message[USER][ACCOUNT_NAME] = account_name
    return message


def handle_response(message):
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise ValueError


def main():
    server_address, server_port = create_parser(LOGGER)

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.connect((server_address, server_port))
    server_addr = transport.getsockname()
    LOGGER.info(f'Server started at {server_addr[0]}:{server_addr[1]}')

    presence_message = create_message(USER_TEST)
    LOGGER.debug('Message created')
    send_message(transport, presence_message)
    LOGGER.debug('The message has been sent')
    try:
        response = get_message(transport)
        LOGGER.debug(f'Message received: {response}')
        hanlded_response = handle_response(response)
        LOGGER.debug(f'Message: {hanlded_response}')
    except (ValueError, json.JSONDecodeError):
        LOGGER.error('Message decoding error')


if __name__ == '__main__':
    main()
