import socket
import select
import logging
import logs.config_server_log
import common.jim as jim

from common.decorators import log
from common.config import (ACTION, ACTION_PRESENCE, ACTION_MESSEGE,
                           MAX_CONNECTIONS, LOGGER_SERVER, SENDER, USER,
                           ACCOUNT_NAME, ERROR, RECIPIENT, ACTION_EXIT)
from common.utils import get_message, send_message, create_parser


LOGGER = logging.getLogger(LOGGER_SERVER)


def handle_message(message, client):
    LOGGER.debug(
        f'Processing of the message from the client has begun : {message}')
    if message.keys() == jim.PRESENCE.keys():
        return message
    elif message.keys() == jim.MESSAGE.keys():
        return message
    elif message.keys() == jim.MESSAGE_EXIT.keys():
        return message
    else:
        LOGGER.error('Invalid request received')
        send_message(client, jim.RESPONSE_400)
        raise Exception


def add_name_client(message, names, client):
    if message[USER][ACCOUNT_NAME] not in names.keys():
        names[message[USER][ACCOUNT_NAME]] = client
        LOGGER.debug(f'added username {message[USER][ACCOUNT_NAME]}')
    else:
        LOGGER.error(
            f'The username is {names[message[USER][ACCOUNT_NAME]]} already taken.')
        response = jim.RESPONSE_400
        response[ERROR] = 'The username is already taken.'
        send_message(client, response)
        raise Exception


def clear_names_clients(names, clients):
    names_del = []
    if names:
        for k, v in names.items():
            if v not in clients:
                names_del.append(k)
        for n in names_del:
            del names[n]
            LOGGER.info(f'Clear username {n}')


def get_client_for_sending_message(recipient, names):
    if recipient in names and names[recipient]:
        return names[recipient]
    else:
        LOGGER.error(
            f'The user {recipient} is not registered '
            f'on the server, sending the message is not possible.')
        return False


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
    messages_list = []
    names_clients = {}

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
                    message = handle_message(msg, client_message)
                    if message[ACTION] == ACTION_PRESENCE:
                        clear_names_clients(names_clients, clients)
                        add_name_client(message, names_clients, client_message)
                        send_message(client_message, jim.RESPONSE_200)
                    elif message[ACTION] == ACTION_MESSEGE:
                        messages_list.append(message)
                    elif message[ACTION] == ACTION_EXIT:
                        clients.remove(client_message)
                        del names_clients[message[ACCOUNT_NAME]]
                except Exception as error:
                    print(error)
                    LOGGER.debug(
                        f'The connection with the client was lost')
                    clients.remove(client_message)
            print([i for i in names_clients.keys()])

        for message in messages_list:
            try:
                pass
                client = get_client_for_sending_message(
                    message[RECIPIENT], names_clients)
                if client:
                    send_message(client, message)
                else:
                    send_message(
                        names_clients[message[SENDER]], jim.RESPONSE_404)
            except:
                LOGGER.debug(
                    f'The connection with the client was lost')
                clients.remove(client)
                clear_names_clients(names_clients, clients)
        messages_list.clear()


if __name__ == '__main__':
    main()
