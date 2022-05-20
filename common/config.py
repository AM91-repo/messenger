import logging
import sys


DEFAULT_IP_ADDRESS = "localhost"
DEFAULT_PORT = 7778
MAX_CONNECTIONS = 5
MAX_PACKAGE_LENGTH = 1024

ENCODING = "utf-8"

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
ACTION_PRESENCE = "presence"
ACTION_MESSEGE = "msg"
ACTION_EXIT = "exit"
RESPONSE = "response"
ERROR = "error"
MESSAGE = "message"

LOGGER_CLIENT = "client"
LOG_CLIENT_FILE = "client.log"
LOGGER_SERVER = "server"
LOG_SERVER_FILE = "server.log"
LOGGING_LEVEL = logging.DEBUG
LOGGING_HANDLER_LEVEL = logging.ERROR
HANDLER_LEVEL = sys.stderr
FORMAT_LOG = "%(asctime)s %(levelname)s %(filename)s %(message)s"
