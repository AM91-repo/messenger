import sys
import json
import socket
import logging
import logs.config_server_log
import common.jim as jim

from common.config import (USER, ACCOUNT_NAME, RESPONSE, ERROR, MAX_CONNECTIONS,
                           LOGGER_SERVER, USER_TEST)
from common.utils import get_message, send_message, create_parser


LOGGER = logging.getLogger(LOGGER_SERVER)


def handle_message(message):
    LOGGER.debug(f'Processing of the message from the client has begun : {message}')
    if message.keys() == jim.PRESENCE.keys() \
            and message[USER][ACCOUNT_NAME] == USER_TEST:
        return {RESPONSE: 200}
    return {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }


def get_server_socket(addr, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((addr, port))
    s.listen(MAX_CONNECTIONS)

    server_addr = s.getsockname()
    LOGGER.info(f'Server started at {server_addr[0]}:{server_addr[1]}')

    return s


def main():
    parser = create_parser()
    argv = parser.parse_args()

    try:
        if not 65535 >= argv.port >= 1024:
            raise ValueError
    except ValueError:
        LOGGER.critical('The port must be specified in the range from 1024 to 65535')
        sys.exit(1)

    transport = get_server_socket(argv.addr, argv.port)

    while True:
        client, client_address = transport.accept()
        LOGGER.debug(f"A client with the address has connected: {client_address}")
        try:
            message = get_message(client)
            LOGGER.debug(f'Message received: {message}')
            response = handle_message(message)
            LOGGER.debug(f'A response to the client has been formed: {response}')
            send_message(client, response)
            LOGGER.debug('The message has been sent')
            client.close()
            LOGGER.debug(f'The connection with the client {client_address} closes')
        except (ValueError, json.JSONDecodeError):
            LOGGER.error('An incorrect message from the client has been received')
            client.close()


if __name__ == '__main__':
    main()
