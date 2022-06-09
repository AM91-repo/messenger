from email import message
import os
import sys
import socket
import select
import logging
import logs.config_server_log
import configparser
import threading
import common.jim as jim

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from database.server_database import ServerDB
from common.metaclasses import ServerMaker
from common.descrptrs import Port, Addr
from common.decorators import log
from common.config import (ACTION, ACTION_PRESENCE, ACTION_MESSEGE,
                           MAX_CONNECTIONS, LOGGER_SERVER, SENDER, USER,
                           ACCOUNT_NAME, ERROR, RECIPIENT, ACTION_EXIT,
                           GET_CONTACTS, ADD_CONTACT, REMOVE_CONTACT,
                           USERS_REQUEST, LIST_INFO)
from common.utils import get_message, send_message, create_parser


LOGGER = logging.getLogger(LOGGER_SERVER)

NEW_CONNECTION = False
CONFLAG_LOCK = threading.Lock()


class Server(threading.Thread, metaclass=ServerMaker):
    port = Port()
    addr = Addr()

    def __init__(self, address, port, database):
        self.addr = address
        self.port = port

        self.database = database

        self.clients = []
        self.messages_list = []
        self.names_clients = {}

        self.message = {}

        super().__init__()

    def socket_initialization(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.addr, self.port))
        s.listen(MAX_CONNECTIONS)
        s.settimeout(0.2)

        self.sock = s

        server_addr = self.sock.getsockname()
        LOGGER.info(f'Server started at {server_addr[0]}:{server_addr[1]}')

    def add_name_client(self, client):
        if self.message[USER][ACCOUNT_NAME] not in self.names_clients.keys():
            self.names_clients[self.message[USER][ACCOUNT_NAME]] = client
            LOGGER.debug(f'added username {self.message[USER][ACCOUNT_NAME]}')
        else:
            LOGGER.error(
                f'The username is {self.names_clients[self.message[USER][ACCOUNT_NAME]]} already taken.')
            response = jim.RESPONSE_400
            response[ERROR] = 'The username is already taken.'
            send_message(client, response)
            raise Exception

    def clear_names_clients(self):
        names_del = []
        if self.names_clients:
            for k, v in self.names_clients.items():
                if v not in self.clients:
                    names_del.append(k)
            for n in names_del:
                del self.names_clients[n]
                LOGGER.info(f'Clear username {n}')

    def get_client_for_sending_message(self, recipient):
        if recipient in self.names_clients and self.names_clients[recipient]:
            return self.names_clients[recipient]
        else:
            LOGGER.error(
                f'The user {recipient} is not registered '
                f'on the server, sending the message is not possible.')
            return False

    def checking_message(self, message, client):
        LOGGER.debug(
            f'Processing of the message from the client has begun : {message}')
        if message.keys() == jim.PRESENCE.keys():
            self.message = message
        elif message.keys() == jim.MESSAGE.keys():
            self.message = message
        elif message.keys() == jim.MESSAGE_EXIT.keys():
            self.message = message
        elif message.keys() == jim.REQUEST_CONTACTS.keys():
            self.message = message
        elif message.keys() == jim.ADDING_CONTACT.keys():
            self.message = message
        elif message.keys() == jim.REMOVE_CONTACT.keys():
            self.message = message
        elif message.keys() == jim.USERS_REQUEST.keys():
            self.message = message
        else:
            LOGGER.error('Invalid request received')
            send_message(client, jim.RESPONSE_400)
            raise Exception

    def processing_client_messages(self, client_sock):
        global NEW_CONNECTION
        msg = get_message(client_sock)
        self.checking_message(msg, client_sock)
        # print(self.message)

        # If this is a presence message
        if self.message[ACTION] == ACTION_PRESENCE:
            self.clear_names_clients()
            self.add_name_client(client_sock)
            client_ip, client_port = client_sock.getpeername()
            self.database.user_login(
                self.message[USER][ACCOUNT_NAME], client_ip, client_port)
            send_message(client_sock, jim.RESPONSE_200)
            with CONFLAG_LOCK:
                NEW_CONNECTION = True

        # If this is a message, then add it to the message queue
        elif self.message[ACTION] == ACTION_MESSEGE:
            if self.message[RECIPIENT] in self.names_clients:
                self.messages_list.append(self.message)
                self.database.process_message(
                    self.message[SENDER], self.message[RECIPIENT])
                send_message(client_sock, jim.RESPONSE_200)
            else:
                response = jim.RESPONSE_400
                response[ERROR] = 'The user is not registered on the server.'
                send_message(client_sock, response)
            return

        # If the client exits
        elif self.message[ACTION] == ACTION_EXIT:
            self.database.user_logout(self.message[ACCOUNT_NAME])
            self.clients.remove(client_sock)
            del self.names_clients[self.message[ACCOUNT_NAME]]
            with CONFLAG_LOCK:
                NEW_CONNECTION = True

        # Contact list request
        elif self.message[ACTION] == GET_CONTACTS:
            response = jim.RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(
                self.message[USER])
            send_message(client_sock, response)

        # adding a contact
        elif self.message[ACTION] == ADD_CONTACT:
            self.database.add_contact(
                self.message[USER], self.message[ACCOUNT_NAME])
            send_message(client_sock, jim.RESPONSE_200)

        # deleting a contact
        elif self.message[ACTION] == REMOVE_CONTACT:
            self.database.remove_contact(
                self.message[USER], self.message[ACCOUNT_NAME])
            send_message(client_sock, jim.RESPONSE_200)

        # request for famous users
        elif self.message[ACTION] == USERS_REQUEST:
            response = jim.RESPONSE_202
            response[LIST_INFO] = [user[0]
                                   for user in self.database.users_list()]
            send_message(client_sock, response)

    def run(self):
        self.socket_initialization()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                LOGGER.debug(
                    f"A client with the address has connected: {client_address}")
                self.clients.append(client)

            clients_messages = []
            waiting_clients = []
            err = []

            try:
                if self.clients:
                    clients_messages, waiting_clients, err = select.select(
                        self.clients, self.clients, [], 0
                    )
            except OSError:
                pass

            if clients_messages:
                for client_message in clients_messages:
                    try:
                        self.processing_client_messages(client_message)
                    except Exception as error:
                        print(error)
                        LOGGER.debug(
                            f'The connection with the client was lost')
                        self.clients.remove(client_message)
                # print([i for i in self.names_clients.keys()])

            for message in self.messages_list:
                try:
                    pass
                    client = self.get_client_for_sending_message(
                        message[RECIPIENT])
                    if client:
                        send_message(client, message)
                    else:
                        send_message(
                            self.names_clients[message[SENDER]], jim.RESPONSE_404)
                except:
                    LOGGER.debug(
                        f'The connection with the client was lost')
                    self.clients.remove(client)
                    self.clear_names_clients()
            self.messages_list.clear()


def main():
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    address, port, _ = create_parser(LOGGER,
                                     config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    db_file = os.path.join(
        config['SETTINGS']['Database_path'],
        config['SETTINGS']['Database_file'])

    database = ServerDB(db_file)

    server = Server(address, port, database)
    server.daemon = True
    server.start()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        global NEW_CONNECTION
        # print(NEW_CONNECTION)
        if NEW_CONNECTION:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with CONFLAG_LOCK:
                NEW_CONNECTION = False

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec_()


if __name__ == '__main__':
    main()
