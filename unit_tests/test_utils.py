import json
import os
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.join(os.getcwd(), '..'))

from common.utils import create_parser, get_message, send_message
from common.config import (ACCOUNT_NAME, ACTION, DEFAULT_IP_ADDRESS,
                           DEFAULT_PORT, ENCODING, ERROR, PRESENCE, RESPONSE,
                           TIME, USER, TYPE)

class SocketSimulation:
    '''
    A test class for testing sending and receiving, 
    when created, requires a dictionary that will be 
    run through the test function
    '''

    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.receved_message = None

    def send(self, message_to_send):
        json_test_message = json.dumps(self.test_dict)
        self.encoded_message = json_test_message.encode(ENCODING)
        self.receved_message = message_to_send

    def recv(self, max_len):
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode(ENCODING)


class Tests(unittest.TestCase):
    '''
    A test class performing testing.
    '''
    test_dict_send = {
        ACTION: PRESENCE,
        TIME: 111111.111111,
        TYPE: 'status',
        USER: {
            ACCOUNT_NAME: 'test_test'
        }
    }
    test_dict_recv_ok = {RESPONSE: 200}
    test_dict_recv_err = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }
    test_list_parser = [
        DEFAULT_IP_ADDRESS,
        DEFAULT_PORT,
    ]

    def test_send_message(self):
        test_socket = SocketSimulation(self.test_dict_send)
        send_message(test_socket, self.test_dict_send)

        self.assertEqual(test_socket.encoded_message,
                         test_socket.receved_message)

    def test_get_message(self):
        test_sock_ok = SocketSimulation(self.test_dict_recv_ok)
        test_sock_err = SocketSimulation(self.test_dict_recv_err)

        self.assertEqual(get_message(test_sock_ok), self.test_dict_recv_ok)

        self.assertEqual(get_message(test_sock_err), self.test_dict_recv_err)


    def test_with_mock_patch_create_parser_default(self):
        with patch.object(sys, 'argv', ['common/utils.py']):
            parser = create_parser()
            argv = parser.parse_args()
            self.assertEqual(self.test_list_parser, [argv.addr, argv.port])


    @patch.object(sys, 'argv', ['common/utils.py', '-p', '2222', '-a', '127.0.0.2'])
    def test_with_mock_patch_create_parser_argv(self):
        parser = create_parser()
        argv = parser.parse_args()
        self.assertEqual(['127.0.0.2', 2222], [argv.addr, argv.port])


if __name__ == '__main__':
    unittest.main()
