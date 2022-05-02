import json
import socket
from time import process_time_ns
import common.jim as jim

from common.config import *
from common.utils import get_message, send_message, create_parser


def handle_message(message):
    if message.keys() == jim.PRESENCE.keys() \
            and message[USER][ACCOUNT_NAME] == 'Guest':
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
    print(f'Server started at {server_addr[0]}:{server_addr[1]}')

    return s


def main():
    parser = create_parser()
    argv = parser.parse_args()

    transport = get_server_socket(argv.addr, argv.port)

    while True:
        client, client_address = transport.accept()
        print(f"Подключился клиент с адресом: {client_address}")
        try:
            message = get_message(client)
            response = handle_message(message)
            send_message(client, response)
            client.close()
        except (ValueError, json.JSONDecodeError):
            print('Принято некорретное сообщение от клиента')
            client.close()


if __name__ == '__main__':
    main()
