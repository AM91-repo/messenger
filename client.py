import json
from multiprocessing.spawn import import_main_path
import socket
import logging
import threading
import time

import logs.config_client_log
import common.jim as jim

from common.metaclasses import ClientMaker
from common.decorators import log
from common.config import (USER, ACCOUNT_NAME, RESPONSE, ERROR, LOGGER_CLIENT,
                           RECIPIENT, MESSAGE, SENDER)
from common.utils import send_message, get_message, create_parser

LOGGER = logging.getLogger(LOGGER_CLIENT)


class ClientSendMessage(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        self._message = {}
        super().__init__()

    def run(self):
        print(f'Client: {self.account_name}')
        print('Supported commands:')
        print('m - send a message')
        print('exit - exiting the program')
        while True:
            command = input('Enter the command: ')
            if command == 'm':
                to_user = input('Enter the recipient of the message: ')
                written_message = input('Enter the message to send: ')
                self.create_message(to_user, written_message)
                send_message(self.sock, self._message)
            elif command == 'exit':
                message_exit = jim.MESSAGE_EXIT
                message_exit[ACCOUNT_NAME] = self.account_name
                send_message(self.sock, message_exit)
                print('Connection termination.')
                LOGGER.info("Completion of work on the user's command.")
                time.sleep(0.5)
                break
            else:
                print(
                    'The command is not recognized, try again.')

    def create_message(self, to_user, client_message):
        self._message = jim.MESSAGE
        self._message[SENDER] = self.account_name
        self._message[RECIPIENT] = to_user
        self._message[MESSAGE] = client_message


class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def run(self):
        while True:
            try:
                message = get_message(self.sock)
                if message.keys() == jim.MESSAGE.keys() and message[RECIPIENT] == self.account_name:
                    print(
                        f'\nReceived a message from the user {message[SENDER]}:\n{message[MESSAGE]}')
                    LOGGER.info(
                        f'Received a message from the user {message[SENDER]}:\n{message[MESSAGE]}')
                elif message.keys() == jim.RESPONSE_404.keys():
                    print(f'The server sent a {message[RESPONSE]} response')
                else:
                    LOGGER.error(
                        f'An incorrect message was received from the server: {message}')
            except:
                LOGGER.critical(f'The connection to the server is lost.')
                break


def create_message(to_user, client_message, account_name):
    message = jim.MESSAGE
    message[SENDER] = account_name
    message[RECIPIENT] = to_user
    message[MESSAGE] = client_message
    return message


def create_presence_message(account_name):
    message = jim.PRESENCE
    message[USER][ACCOUNT_NAME] = account_name
    return message


def handle_response(message):
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            return ValueError
    raise ValueError


def message_written_client():
    message = jim.MESSAGE
    message[MESSAGE] = input('Enter the message to send: ')
    return message


def main():
    server_address, server_port, name = create_parser(LOGGER)

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.connect((server_address, server_port))
    server_addr = transport.getsockname()
    LOGGER.info(f'Сonnecting to the server {server_addr[0]}:{server_addr[1]}')

    presence_message = create_presence_message(name)
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
        exit(1)
    else:

        receiver = ClientReader(name, transport)
        receiver.daemon = True
        receiver.start()

        user_interface = ClientSendMessage(name, transport)
        user_interface.daemon = True
        user_interface.start()
        LOGGER.debug('Processes are running')

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
