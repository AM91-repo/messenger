import socket
import select
import logging
import logs.config_server_log
import common.jim as jim

from database.server_database import ServerStorage
from common.metaclasses import ServerMaker
from common.descrptrs import Port, Addr
from common.decorators import log
from common.config import (ACTION, ACTION_PRESENCE, ACTION_MESSEGE,
                           MAX_CONNECTIONS, LOGGER_SERVER, SENDER, USER,
                           ACCOUNT_NAME, ERROR, RECIPIENT, ACTION_EXIT)
from common.utils import get_message, send_message, create_parser


LOGGER = logging.getLogger(LOGGER_SERVER)


class Server(metaclass=ServerMaker):
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

    def socket_initialization(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.addr, self.port))
        s.listen(MAX_CONNECTIONS)
        s.settimeout(0.2)

        self.sock = s

        server_addr = self.sock.getsockname()
        LOGGER.info(f'Server started at {server_addr[0]}:{server_addr[1]}')

    def checking_message(self, message, client):
        LOGGER.debug(
            f'Processing of the message from the client has begun : {message}')
        if message.keys() == jim.PRESENCE.keys():
            self.message = message
        elif message.keys() == jim.MESSAGE.keys():
            self.message = message
        elif message.keys() == jim.MESSAGE_EXIT.keys():
            self.message = message
        else:
            LOGGER.error('Invalid request received')
            send_message(client, jim.RESPONSE_400)
            raise Exception

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

    def interaction_with_client(self, sock):
        msg = get_message(sock)
        self.handle_message(msg, sock)
        print(self.message)
        if self.message[ACTION] == ACTION_PRESENCE:
            self.clear_names_clients()
            self.add_name_client(sock)
            client_ip, client_port = sock.getpeername()
            self.database.user_login(
                self.message[USER][ACCOUNT_NAME], client_ip, client_port)
            send_message(sock, jim.RESPONSE_200)
        elif self.message[ACTION] == ACTION_MESSEGE:
            self.messages_list.append(self.message)
        elif self.message[ACTION] == ACTION_EXIT:
            self.clients.remove(sock)
            del self.names_clients[self.message[ACCOUNT_NAME]]

    def processing_client_messages(self, client_sock):
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
        # If this is a message, then add it to the message queue
        elif self.message[ACTION] == ACTION_MESSEGE:
            self.messages_list.append(self.message)
        # If the client exits
        elif self.message[ACTION] == ACTION_EXIT:
            self.database.user_logout(self.message[ACCOUNT_NAME])
            self.clients.remove(client_sock)
            del self.names_clients[self.message[ACCOUNT_NAME]]

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
    address, port, _ = create_parser(LOGGER)

    database = ServerStorage()

    server = Server(address, port, database)
    server.run()


if __name__ == '__main__':
    main()
