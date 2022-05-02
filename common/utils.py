import json
import argparse

from common.config import ENCODING, MAX_PACKAGE_LENGTH, DEFAULT_IP_ADDRESS, DEFAULT_PORT


def create_parser():
    parser = argparse.ArgumentParser()

    parser_group = parser.add_argument_group(title='Parameters')
    parser_group.add_argument('-a', '--addr',
                              default=DEFAULT_IP_ADDRESS, help='IP address')
    parser_group.add_argument('-p', '--port', type=int,
                              default=DEFAULT_PORT, help='TCP port')

    return parser


def send_message(opened_socket, message):
    json_message = json.dumps(message)
    response = json_message.encode(ENCODING)
    opened_socket.send(response)


def get_message(opened_socket):
    response = opened_socket.recv(MAX_PACKAGE_LENGTH)
    if isinstance(response, bytes):
        json_response = response.decode(ENCODING)
        response_dict = json.loads(json_response)
        if isinstance(response_dict, dict):
            return response_dict
        raise ValueError
    raise ValueError
