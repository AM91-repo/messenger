from email import message
import socket
import sys
import time
import logging
import json
import threading
import hashlib
import hmac
import binascii
from PyQt5.QtCore import pyqtSignal, QObject

sys.path.append('../')
import common.jim as jim
from common.errors import ServerError
from common.utils import send_message, get_message
from common.config import (USER, ACCOUNT_NAME, RESPONSE, ERROR, LOGGER_CLIENT, DATA,
                           RECIPIENT, MESSAGE, SENDER, LIST_INFO, TIME, PUBLIC_KEY)


LOGGER = logging.getLogger(LOGGER_CLIENT)
SOCK_LOCK = threading.Lock()


# Transport class, responsible for interacting with the server
class ClientTransport(threading.Thread, QObject):
    '''
    A class implementing the transport subsystem of the client
    module. Responsible for interacting with the server.
    '''
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()
    message_205 = pyqtSignal()

    def __init__(self, port, ip_address, database, account_name, passwd, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.account_name = account_name
        self.password = passwd
        self.transport = None
        self.keys = keys
        self.connection_init(port, ip_address)
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                LOGGER.critical(f'The connection to the server is lost.')
                raise ServerError('The connection to the server is lost.')
            LOGGER.error('Timeout connections when updating user lists.')
        except json.JSONDecodeError:
            LOGGER.critical(f'The connection to the server is lost.')
            raise ServerError('The connection to the server is lost.')

        self.running = True

    def connection_init(self, port, ip):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.transport.settimeout(5)

        connected = False
        for i in range(5):
            LOGGER.info(f'Connection attempt №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        if not connected:
            LOGGER.critical('Failed to establish a connection with the server')
            raise ServerError('Failed to establish a connection with the server')

        LOGGER.debug('Starting auth dialog.')

        passwd_bytes = self.password.encode('utf-8')
        salt = self.account_name.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)

        LOGGER.debug(f'Passwd hash ready: {passwd_hash_string}')

        pubkey = self.keys.publickey().export_key().decode('ascii')

        with SOCK_LOCK:
            presense = jim.PRESENCE
            presense[TIME] = time.time()
            presense[USER][ACCOUNT_NAME] = self.account_name
            presense[USER][PUBLIC_KEY] = pubkey
            LOGGER.debug(f"Presense message = {presense}")

            try:
                send_message(self.transport, presense)
                ans = get_message(self.transport)
                LOGGER.debug(f'Server response = {ans}.')

                if RESPONSE in ans:
                    if ans[RESPONSE] == 400:
                        raise ServerError(ans[ERROR])
                    elif ans[RESPONSE] == 511:
                        ans_data = ans[DATA]
                        hash = hmac.new(passwd_hash_string, ans_data.encode('utf-8'), 'MD5')
                        digest = hash.digest()
                        my_ans = jim.RESPONSE_511
                        my_ans[DATA] = binascii.b2a_base64(
                            digest).decode('ascii')
                        send_message(self.transport, my_ans)
                        msg = get_message(self.transport)
                        self.handle_response(msg)
            except (OSError, json.JSONDecodeError) as err:
                LOGGER.debug(f'Connection error.', exc_info=err)
                raise ServerError('Connection failure during authorization.')



    def create_presence(self):
        message = jim.PRESENCE
        message[TIME] = time.time()
        message[USER][ACCOUNT_NAME] = self.account_name
        LOGGER.debug(f'Sent presence message from user {self.account_name}')
        return message

    def handle_response(self, message):
        LOGGER.debug(f'Parsing a message from the server: {message}')
        print('get')

        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(f'{message[ERROR]}')
            elif message[RESPONSE] == 205:
                self.user_list_update()
                self.contacts_list_update()
                self.message_205.emit()
            else:
                LOGGER.debug(f'Unknown confirmation code received {message[RESPONSE]}')

        elif message.keys() == jim.MESSAGE.keys() and \
                message[RECIPIENT] == self.account_name:
            LOGGER.debug(f'Received a message from the user {message[SENDER]}:{message[MESSAGE]}')
            self.database.save_message(message[SENDER] , 'in' , message[MESSAGE])
            self.new_message.emit(message[SENDER])

    def contacts_list_update(self):
        LOGGER.debug(f'Request a contact sheet for the user {self.account_name}')
        req = jim.REQUEST_CONTACTS
        req[TIME] = time.time()
        req[USER] = self.account_name
        LOGGER.debug(f'A request has been formed {req}')

        with SOCK_LOCK:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        LOGGER.debug(f'Response received {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            LOGGER.error('Failed to update contact list.')

    def user_list_update(self):
        LOGGER.debug(f'Requesting a list of known users {self.account_name}')
        req = jim.USERS_REQUEST
        req[TIME] = time.time()
        req[ACCOUNT_NAME] = self.account_name

        with SOCK_LOCK:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.database.add_users(ans[LIST_INFO])
        else:
            LOGGER.error('Failed to update the list of known users.')

    def add_contact(self, contact):
        LOGGER.debug(f'Creating a contact {contact}')
        req = jim.ADDING_CONTACT
        req[TIME] = time.time()
        req[USER] = self.account_name
        req[ACCOUNT_NAME] = contact
        with SOCK_LOCK:
            send_message(self.transport, req)
            self.handle_response(get_message(self.transport))

    def remove_contact(self, contact):
        LOGGER.debug(f'Deleting a contact {contact}')
        req = jim.REMOVE_CONTACT
        req[TIME] = time.time()
        req[USER] = self.account_name
        req[ACCOUNT_NAME] = contact
        with SOCK_LOCK:
            send_message(self.transport, req)
            self.handle_response(get_message(self.transport))

    def transport_shutdown(self):
        self.running = False
        message = jim.MESSAGE_EXIT
        message[TIME] = time.time()
        message[ACCOUNT_NAME] = self.account_name
        with SOCK_LOCK:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        LOGGER.debug('Transport is shutting down.')
        time.sleep(0.5)

    # Функция отправки сообщения на сервер
    def send_message(self, to, user_message):
        message = jim.MESSAGE
        message[SENDER] = self.account_name
        message[RECIPIENT] = to
        message[TIME] = time.time()
        message[MESSAGE] = user_message
        LOGGER.debug(f'The message dictionary has been formed: {message}')

        with SOCK_LOCK:
            send_message(self.transport, message)
            print('send')
            self.handle_response(get_message(self.transport))
            LOGGER.info(f'A message has been sent to the user {to}')

    def run(self):
        LOGGER.debug('The process - receiver of messages from the server is started.')
        while self.running:
            time.sleep(1)
            with SOCK_LOCK:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        LOGGER.critical(f'The connection to the server is lost.')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    LOGGER.debug(f'The connection to the server is lost.')
                    self.running = False
                    self.connection_lost.emit()
                else:
                    LOGGER.debug(f'Received a message from the server: {message}')
                    self.handle_response(message)
                finally:
                    self.transport.settimeout(5)