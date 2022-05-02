from email import message
import json
import sys
import socket
import common.jim as jim

from common.config import *
from common.utils import send_message, get_message


def create_message(account_name):
    message = jim.PRESENCE
    message[USER][ACCOUNT_NAME] = account_name
    return message


def handle_response(message):
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise ValueError


def get_server_addr_port():
    try:
        address = sys.argv[1]
        port = int(sys.argv[2])
        if not 65535 >= port >= 1024:
            raise ValueError
    except IndexError:
        address = DEFAULT_IP_ADDRESS
        port = DEFAULT_PORT
    except ValueError:
        print('Порт должен быть указан в пределах от 1024 до 65535')
        sys.exit(1)
    return address, port


def main():
    server_address, server_port = get_server_addr_port()

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.connect((server_address, server_port))
    presence_message = create_message('Guest')
    send_message(transport, presence_message)
    try:
        response = get_message(transport)
        hanlded_response = handle_response(response)
        print(f'Ответ от сервера: {response}')
        print(hanlded_response)
    except (ValueError, json.JSONDecodeError):
        print('Ошибка декодирования сообщения')


if __name__ == '__main__':
    main()
