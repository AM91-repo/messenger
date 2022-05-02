import sys
import os
import logging
import logging.handlers
from common.config import (LOGGING_LEVEL, HANDLER_LEVEL, LOGGING_HANDLER_LEVEL,
                           FORMAT_LOG, ENCODING, LOGGER_SERVER, LOG_SERVER_FILE)

sys.path.append('../')

FORMATTER = logging.Formatter(FORMAT_LOG)

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, LOG_SERVER_FILE)

HANDLER = logging.StreamHandler(HANDLER_LEVEL)
HANDLER.setFormatter(FORMATTER)
HANDLER.setLevel(LOGGING_HANDLER_LEVEL)
LOG_FILE = logging.handlers.TimedRotatingFileHandler(PATH, encoding=ENCODING, interval=1, when='D')
LOG_FILE.setFormatter(FORMATTER)

LOG = logging.getLogger(LOGGER_SERVER)
LOG.addHandler(HANDLER)
LOG.addHandler(LOG_FILE)
LOG.setLevel(LOGGING_LEVEL)


if __name__ == '__main__':
    LOG.critical('Критическая ошибка')
    LOG.error('Ошибка')
    LOG.debug('Отладочная информация')
    LOG.info('Информационное сообщение')
