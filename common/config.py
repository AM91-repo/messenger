import logging
import sys
import os


DEFAULT_IP_ADDRESS = "localhost"
DEFAULT_PORT = 7777
MAX_CONNECTIONS = 5
MAX_PACKAGE_LENGTH = 1024

ENCODING = "utf-8"

SERVER_DATABASE = f'sqlite:///database/server.db3'

CLIENT_MODE_LISTEN = "listen"
CLIENT_MODE_SEND = "send"

ACTION = "action"
TIME = "time"
USER = "user"
TYPE = "type"
ACCOUNT_NAME = "account_name"
SENDER = 'from'
RECIPIENT = 'to'

USER_TEST = "Guest"
RESPONSE = "response"
ACTION_PRESENCE = "presence"
ACTION_MESSEGE = "msg"
ACTION_EXIT = "exit"
RESPONSE = "response"
ERROR = "error"
MESSAGE = "message"
GET_CONTACTS = "get_contacts"
LIST_INFO = "data_list"
REMOVE_CONTACT = "remove"
ADD_CONTACT = "add"
USERS_REQUEST = "get_users"
PUBLIC_KEY = "pubkey"
PUBLIC_KEY_REQUEST = 'pubkey_need'
DATA = "bin"

LOGGER_CLIENT = "client"
LOG_CLIENT_FILE = "client.log"
LOGGER_SERVER = "server"
LOG_SERVER_FILE = "server.log"
LOGGING_LEVEL = logging.DEBUG
LOGGING_HANDLER_LEVEL = logging.ERROR
HANDLER_LEVEL = sys.stderr
FORMAT_LOG = "%(asctime)s %(levelname)s %(filename)s %(message)s"
