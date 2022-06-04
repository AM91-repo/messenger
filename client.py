import json
from multiprocessing.spawn import import_main_path
import socket
import logging
import threading
import time
from datetime import datetime

import logs.config_client_log
import common.jim as jim

from database.client_database import ClientDatabase

from common.errors import ServerError, IncorrectDataRecivedError
from common.metaclasses import ClientMaker
from common.decorators import log
from common.config import (USER, ACCOUNT_NAME, RESPONSE, ERROR, LOGGER_CLIENT,
                           RECIPIENT, MESSAGE, SENDER, LIST_INFO, TIME)
from common.utils import send_message, get_message, create_parser

LOGGER = logging.getLogger(LOGGER_CLIENT)

SOCK_LOCK = threading.Lock()
DB_LOCK = threading.Lock()


class ClientSendMessage(threading.Thread, metaclass=ClientMaker):
    MESSAGE_COMMAND = 'm'
    HISTORY_COMMAND = 'h'
    CONTACT_COMMAND = 'c'
    EDIT_COMMAND = 'edit'
    HELP_COMMAND = 'help'
    EXIT_COMMAND = 'exit'

    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self._message = {}
        self.database = database
        super().__init__()

    def print_help(self):
        print('Supported commands:')
        print(f'{self.MESSAGE_COMMAND} - send a message')
        print(f'{self.HISTORY_COMMAND} - message history')
        print(f'{self.CONTACT_COMMAND} - contact list')
        print(f'{self.EDIT_COMMAND} - editing the contact list')
        print(f'{self.HELP_COMMAND} - output hints by commands')
        print(f'{self.EXIT_COMMAND} - exiting the program')

    def run(self):
        print(f'Client: {self.account_name}')
        self.print_help()
        while True:
            command = input('Enter the command: ')
            if command == self.MESSAGE_COMMAND:
                to_user = input('Enter the recipient of the message: ')
                written_message = input('Enter the message to send: ')
                self.create_message(to_user, written_message)

            elif command == self.CONTACT_COMMAND:
                with DB_LOCK:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)
            
            elif command == self.HISTORY_COMMAND:
                self.print_history()

            elif command == self.EDIT_COMMAND:
                self.edit_contacts()

            elif command == self.HELP_COMMAND:
                self.print_help()

            elif command == self.EXIT_COMMAND:
                message_exit = jim.MESSAGE_EXIT
                message_exit[ACCOUNT_NAME] = self.account_name
                with SOCK_LOCK:
                    try:
                        send_message(self.sock, message_exit)
                    except Exception as e:
                        print(e)
                        pass
                    print('Connection termination.')
                    LOGGER.info("Completion of work on the user's command.")
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print(
                    'The command is not recognized, try again.')

    def create_message(self, to_user, client_message):
        with DB_LOCK:
            if not self.database.check_user(to_user):
                LOGGER.error(f'Attempt to send a message '
                             f'to an unregistered recipient: {to_user}')
                return

        self._message = jim.MESSAGE
        self._message[SENDER] = self.account_name
        self._message[TIME] = str(datetime.now().replace(microsecond=0).isoformat(sep=' '))
        self._message[RECIPIENT] = to_user
        self._message[MESSAGE] = client_message

        with DB_LOCK:
            self.database.save_message(self.account_name, to_user, client_message)

        with SOCK_LOCK:
            try:
                send_message(self.sock, self._message)
                LOGGER.info(f'A message has been sent to the user {to_user}')
            except OSError as err:
                if err.errno:
                    LOGGER.critical('The connection to the server is lost.')
                    exit(1)
                else:
                    LOGGER.error('The message could not be transmitted. Connection timeout')

    def print_history(self):
        ask = input('Show incoming messages - in, outgoing - out, all - simply Enter: ')
        with DB_LOCK:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nMessage from the user: {message[0]} '
                          f'от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nMessage to the user: {message[1]} '
                          f'от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nMessage from the user: {message[0]},'
                          f' user {message[1]} '
                          f'from {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('To delete, enter - del, to add - add: ')
        if ans == 'del':
            edit = input('Enter the name of the contact to delete: ')
            with DB_LOCK:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    LOGGER.error('Attempt to delete a non-existent contact.')
        elif ans == 'add':
            edit = input('Enter the name of the contact you are creating: ')
            if self.database.check_user(edit):
                with DB_LOCK:
                    self.database.add_contact(edit)
                with SOCK_LOCK:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except ServerError:
                        LOGGER.error('Failed to send information to the server.')


class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def run(self):
        while True:
            time.sleep(1)
            with SOCK_LOCK:
                try:
                    message = get_message(self.sock)
                except IncorrectDataRecivedError:
                    LOGGER.error(f'The received message could not be decoded.')

                except OSError as err:
                    if err.errno:
                        LOGGER.critical(f'The connection to the server is lost.')
                        break

                except (ConnectionError,
                        ConnectionAbortedError,
                        ConnectionResetError,
                        json.JSONDecodeError):
                    LOGGER.critical(f'The connection to the server is lost.')
                    break
                else:
                    if message.keys() == jim.MESSAGE.keys() and message[RECIPIENT] == self.account_name:
                        print(
                            f'\nReceived a message from the user {message[SENDER]}:\n{message[MESSAGE]}')
                        with DB_LOCK:
                            try:
                                self.database.save_message(message[SENDER],
                                                           self.account_name,
                                                           message[MESSAGE])
                            except Exception as e:
                                print(e)
                                LOGGER.error('Database interaction error')
                        LOGGER.info(
                            f'Received a message from the user {message[SENDER]}:\n{message[MESSAGE]}')
                    elif message.keys() == jim.RESPONSE_404.keys():
                        print(f'The server sent a {message[RESPONSE]} response')
                    else:
                        LOGGER.error(
                            f'An incorrect message was received from the server: {message}')


def create_presence_message(account_name):
    message = jim.PRESENCE
    message[TIME] = str(datetime.now().replace(microsecond=0).isoformat(sep=' '))
    message[USER][ACCOUNT_NAME] = account_name
    return message


def handle_response(message):
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            return ValueError
    raise ValueError


def contacts_list_request(sock, name):
    LOGGER.debug(f'Request a contact sheet for the user {name}')
    req = jim.REQUEST_CONTACTS
    req[TIME] = str(datetime.now().replace(microsecond=0).isoformat(sep=' '))
    req[USER] = name
    LOGGER.debug(f'A request has been formed {req}')
    send_message(sock, req)
    ans = get_message(sock)
    LOGGER.debug(f'Response received {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def add_contact(sock, username, contact):
    LOGGER.debug(f'Creating a contact {contact}')
    req = jim.ADDING_CONTACT
    req[TIME] = str(datetime.now().replace(microsecond=0).isoformat(sep=' '))
    req[USER] = username
    req[ACCOUNT_NAME] = contact
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Error creating a contact')
    print('Successful creation of a contact.')


def user_list_request(sock, username):
    LOGGER.debug(f'Requesting a list of known users {username}')
    req = jim.USERS_REQUEST
    req[TIME] = str(datetime.now().replace(microsecond=0).isoformat(sep=' '))
    req[ACCOUNT_NAME] = username
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def remove_contact(sock, username, contact):
    LOGGER.debug(f'Deleting a contact {contact}')
    req = jim.REMOVE_CONTACT
    req[TIME] = str(datetime.now().replace(microsecond=0).isoformat(sep=' '))
    req[USER] = username
    req[ACCOUNT_NAME] = contact
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Client Deletion Error')
    print('Successful deletion')


def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        LOGGER.error('Error requesting a list of known users.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        LOGGER.error('Contact list request error.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():
    server_address, server_port, name = create_parser(LOGGER)

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.settimeout(1)
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

        database = ClientDatabase(name)
        database_load(transport, database, name)

        user_interface = ClientSendMessage(name, transport, database)
        user_interface.daemon = True
        user_interface.start()
        LOGGER.debug('Processes are running')

        receiver = ClientReader(name, transport, database)
        receiver.daemon = True
        receiver.start()

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
