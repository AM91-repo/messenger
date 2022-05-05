from email import message
from email.headerregistry import Address
import sys
import json
import socket
import select
import logging
from urllib import response
import logs.config_server_log
import common.jim as jim

from common.decorators import log
from common.config import (ACTION_PRESENCE, ACTION_MESSEGE, MAX_CONNECTIONS,
                           LOGGER_SERVER, USER_TEST)
from common.utils import get_message, send_message, create_parser


LOGGER = logging.getLogger(LOGGER_SERVER)


def handle_message(message):
    LOGGER.debug(
        f'Processing of the message from the client has begun : {message}')
    if message.keys() == jim.PRESENCE.keys():
        return jim.RESPONSE_200, ACTION_PRESENCE
    elif message.keys() == jim.MESSAGE.keys():
        return message, ACTION_MESSEGE
    else:
        return jim.RESPONSE_400, ACTION_PRESENCE


def get_server_socket(addr, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((addr, port))
    s.listen(MAX_CONNECTIONS)
    s.settimeout(0.2)

    server_addr = s.getsockname()
    LOGGER.info(f'Server started at {server_addr[0]}:{server_addr[1]}')

    return s


def main():
    address, port, _ = create_parser(LOGGER)
    transport = get_server_socket(address, port)

    clients = []

    while True:
        try:
            client, client_address = transport.accept()
        except OSError:
            pass
        else:
            LOGGER.debug(
                f"A client with the address has connected: {client_address}")
            clients.append(client)

        clients_messages = []
        waiting_clients = []
        err = []

        try:
            if clients:
                clients_messages, waiting_clients, err = select.select(
                    clients, clients, [], 0
                )
        except OSError:
            pass

        if clients_messages:
            for client_message in clients_messages:
                try:
                    msg = get_message(client_message)
                    message, action = handle_message(msg)
                    if action == ACTION_PRESENCE:
                        send_message(client_message, message)
                    elif action == ACTION_MESSEGE:
                        for waiting_client in waiting_clients:
                            try:
                                send_message(waiting_client, message)
                            except:
                                LOGGER.debug(
                                    f'The connection with the client was lost')
                                clients.remove(waiting_client)
                except:
                    LOGGER.debug(
                        f'The connection with the client was lost')
                    clients.remove(client_message)


if __name__ == '__main__':
    main()
