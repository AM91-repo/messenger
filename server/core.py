import threading
import logging
import select
import socket
import json
import hmac
import binascii
import os
import sys

sys.path.append('../')
import common.jim as jim
from common.descrptrs import Port, Addr
from common.decorators import login_required
from common.config import (ACTION, ACTION_EXIT, RESPONSE, MAX_CONNECTIONS, LOGGER_SERVER, SENDER, USER,
                           ACCOUNT_NAME, ERROR, RECIPIENT, LIST_INFO, DATA, PUBLIC_KEY,
                           ADD_CONTACT, USERS_REQUEST, REMOVE_CONTACT, GET_CONTACTS)
from common.utils import get_message, send_message
# Загрузка логера
LOGGER = logging.getLogger(LOGGER_SERVER)


class MessageProcessor(threading.Thread):
    """
    The main class of the server. Accepts connections, dictionaries - packages
    from clients, processes incoming messages.
    Works as a separate thread.
    """
    port = Port()
    addr = Addr()

    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.port = listen_port

        self.database = database
        self.sock = None

        self.clients = []

        self.listen_sockets = None
        self.error_sockets = None

        self.running = True

        self.names = dict()

        super().__init__()

    def run(self):
        '''The method is the main flow cycle.'''
        self.init_socket()

        while self.running:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                LOGGER.info(f'The connection to the PC is established {client_address}')
                client.settimeout(5)
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Проверяем на наличие ждущих клиентов
            try:
                if self.clients:
                    recv_data_lst, self.listen_sockets, self.error_sockets = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as err:
                LOGGER.error(f'Error working with sockets: {err.errno}')

            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(
                            get_message(client_with_message), client_with_message)
                    except (OSError, json.JSONDecodeError, TypeError) as err:
                        LOGGER.debug(f'Getting data from client exception.', exc_info=err)
                        self.remove_client(client_with_message)

    def remove_client(self, client):
        '''
        The handler method of the client with which the connection was interrupted.
        Searches for a client and removes it from the lists and database:
        '''
        LOGGER.info(f'Client {client.getpeername()} disconnected from the server.')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def init_socket(self):
        '''The socket initializer method.'''
        LOGGER.info(
            f'The server is running, the port to connect to: {self.port}.' 
            f'the address from which connections are accepted: {self.addr}.' 
            f'If the address is not specified, connections from any addresses are accepted.')
        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        # Начинаем слушать сокет.
        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def process_message(self, message):
        '''
        The method of sending the message to the client.
        '''
        if message[RECIPIENT] in self.names and self.names[message[RECIPIENT]
        ] in self.listen_sockets:
            try:
                send_message(self.names[message[RECIPIENT]], message)
                LOGGER.info(
                    f'A message was sent to the user {message[RECIPIENT]} from the user {message[SENDER]}.')
            except OSError:
                self.remove_client(message[RECIPIENT])
        elif message[RECIPIENT] in self.names and self.names[message[RECIPIENT]] not in self.listen_sockets:
            LOGGER.error(
                f'Communication with the client {message[RECIPIENT]} was lost. '
                f'The connection is closed, delivery is not possible.')
            self.remove_client(self.names[message[RECIPIENT]])
        else:
            LOGGER.error(
                f'The user {message[RECIPIENT]} is not registered on the server, sending the message is not possible.')

    @login_required
    def process_client_message(self, message, client):
        """ The method is a handler for incoming messages. """

        LOGGER.debug(f'Parsing a message from a client : {message}')
        if message.keys() == jim.PRESENCE.keys():
            self.autorize_user(message, client)

        elif message.keys() == jim.MESSAGE.keys() and self.names[message[SENDER]] == client:
            if message[RECIPIENT] in self.names:
                self.database.process_message(
                    message[SENDER], message[RECIPIENT])
                self.process_message(message)
                try:
                    send_message(client, jim.RESPONSE_200)
                except OSError:
                    self.remove_client(client)
            else:
                response = jim.RESPONSE_400
                response[ERROR] = 'The user is not registered on the server.'
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return

        elif message.keys() == jim.MESSAGE_EXIT.keys() \
            and self.names[message[ACCOUNT_NAME]] == client \
            and message[ACTION] == ACTION_EXIT:
            self.remove_client(client)

        elif message.keys() == jim.REQUEST_CONTACTS.keys() and \
                self.names[message[USER]] == client and \
                message[ACTION] == GET_CONTACTS:
            response = jim.RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        elif message.keys() == jim.ADDING_CONTACT.keys() \
                and self.names[message[USER]] == client and \
                message[ACTION] == ADD_CONTACT:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, jim.RESPONSE_200)
            except OSError:
                self.remove_client(client)

        elif message.keys() == jim.REMOVE_CONTACT.keys() \
                and self.names[message[USER]] == client and \
                message[ACTION] == REMOVE_CONTACT:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, jim.RESPONSE_200)
            except OSError:
                self.remove_client(client)

        elif message.keys() == jim.USERS_REQUEST.keys() \
                and self.names[message[ACCOUNT_NAME]] == client and \
                message[ACTION] == USERS_REQUEST:
            response = jim.RESPONSE_202
            print(message)
            response[LIST_INFO] = [user[0]
                                   for user in self.database.users_list()]
            print(response)
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        elif message.keys() == jim.PUBLIC_KEY_REQUEST.keys():
            response = jim.RESPONSE_511
            response[DATA] = self.database.get_pubkey(message[ACCOUNT_NAME])
            if response[DATA]:
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = jim.RESPONSE_400
                response[ERROR] = 'There is no public key for this user'
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

        else:
            response = jim.RESPONSE_400
            response[ERROR] = 'The request is incorrect.'
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

    def autorize_user(self, message, sock):
        """ Method implementing user authorization. """
        # Если имя пользователя уже занято то возвращаем 400
        LOGGER.debug(f'Start auth process for {message[USER]}')
        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = jim.RESPONSE_400
            response[ERROR] = 'The username is already taken.'
            try:
                LOGGER.debug(f'Username busy, sending {response}')
                send_message(sock, response)
            except OSError:
                LOGGER.debug('OS Error')
                pass
            self.clients.remove(sock)
            sock.close()

        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            response = jim.RESPONSE_400
            response[ERROR] = 'The user is not registered.'
            try:
                LOGGER.debug(f'Unknown username, sending {response}')
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            LOGGER.debug('Correct username, starting passwd check.')

            message_auth = jim.RESPONSE_511
            random_str = binascii.hexlify(os.urandom(64))
            message_auth[DATA] = random_str.decode('ascii')
            hash = hmac.new(self.database.get_hash(message[USER][ACCOUNT_NAME]), random_str, 'MD5')
            digest = hash.digest()
            LOGGER.debug(f'Auth message = {message_auth}')
            try:
                send_message(sock, message_auth)
                ans = get_message(sock)
            except OSError as err:
                LOGGER.debug('Error in auth, data:', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[DATA])
            if RESPONSE in ans and ans[RESPONSE] == 511 and \
                    hmac.compare_digest(digest, client_digest):
                self.names[message[USER][ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, jim.RESPONSE_200)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])
                self.database.user_login(
                    message[USER][ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[USER][PUBLIC_KEY])
            else:
                response = jim.RESPONSE_400
                response[ERROR] = 'Неверный пароль.'
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        '''A method that implements sending a service message to 205 clients.'''
        for client in self.names:
            try:
                send_message(self.names[client], jim.RESPONSE_205)
            except OSError:
                self.remove_client(self.names[client])
