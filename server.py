from email import message
import os
import sys
import socket
import select
import logging
import logs.config_server_log
import configparser
import threading
import common.jim as jim

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from server.main_window import MainWindow
from database.server_database import ServerStorage
from server.core import MessageProcessor
from common.decorators import log
from common.config import LOGGER_SERVER, DEFAULT_PORT
from common.utils import create_parser

LOGGER = logging.getLogger(LOGGER_SERVER)


@log
def config_load():
    """Configuration ini file parser."""
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server_dist+++.ini'}")

    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', 'localhost')
        config.set('SETTINGS', 'Database_path', 'database/')
        config.set('SETTINGS', 'Database_file', 'server.db3')
        return config


def main():
    '''Main function'''
    config = config_load()

    listen_address, listen_port, _, _, gui_flag = create_parser(LOGGER,
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    database = ServerStorage(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))

    server = MessageProcessor(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    if gui_flag:
        while True:
            command = input('Введите exit для завершения работы сервера.')
            if command == 'exit':
                server.running = False
                server.join()
                break

    else:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)

        server_app.exec_()

        server.running = False


if __name__ == '__main__':
    main()
