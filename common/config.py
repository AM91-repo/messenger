import logging
import sys

DEFAULT_IP_ADDRESS = "localhost"
DEFAULT_PORT = 7777
MAX_CONNECTIONS = 5
MAX_PACKAGE_LENGTH = 1024

ENCODING = "utf-8"

ACTION = "action"
TIME = "time"
USER = "user"
TYPE = "type"
ACCOUNT_NAME = "account_name"
USER_TEST = "Guest"

LOGGER_CLIENT = "client"
LOG_CLIENT_FILE = "client.log"
LOGGER_SERVER = "server"
LOG_SERVER_FILE = "server.log"
LOGGING_LEVEL = logging.DEBUG
LOGGING_HANDLER_LEVEL = logging.ERROR
HANDLER_LEVEL = sys.stderr
FORMAT_LOG = "%(asctime)s %(levelname)s %(filename)s %(message)s"


PRESENCE = "presence"
RESPONSE = "response"
ERROR = "error"
