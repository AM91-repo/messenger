import sys
import os
import unittest
from unittest.mock import patch

sys.path.append(os.path.join(os.getcwd(), '..'))

from client import create_message, handle_response
from common.config import (RESPONSE, ERROR, USER, 
                           ACCOUNT_NAME, TIME, ACTION, 
                           PRESENCE, TYPE)


class TestClass(unittest.TestCase):
    '''
    A test class performing testing.
    '''
    def test_def_presense(self):
        """Тест коректного запроса"""
        test = create_message('Guest')
        test[TIME] = 1.1

        self.assertEqual(test, {
                ACTION: PRESENCE, 
                TIME: 1.1, 
                TYPE: 'status', 
                USER: {ACCOUNT_NAME: 'Guest',
                    'status': ''
                    }
            })

    def test_200_ans(self):
        """Тест корректтного разбора ответа 200"""
        self.assertEqual(handle_response({RESPONSE: 200}), '200 : OK')

    def test_400_ans(self):
        """Тест корректного разбора 400"""
        self.assertEqual(handle_response(
            {RESPONSE: 400, ERROR: 'Bad Request'}), '400 : Bad Request')

    def test_no_response(self):
        """Тест исключения без поля RESPONSE"""
        self.assertRaises(ValueError, handle_response, {ERROR: 'Bad Request'})


if __name__ == '__main__':
    unittest.main()
