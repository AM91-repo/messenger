import os
import sys
import logging
import logs.config_client_log

from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox

from database.client_database import ClientDatabase
from common.errors import ServerError
from client.transport import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from common.errors import ServerError
from common.config import LOGGER_CLIENT
from common.utils import create_parser

LOGGER = logging.getLogger(LOGGER_CLIENT)


def main():
    server_address, server_port, name, password, _ = create_parser(LOGGER)

    client_gui = QApplication(sys.argv)

    if not name:
        start_dialog = UserNameDialog()
        client_gui.exec_()
        if start_dialog.ok_pressed:
            name = start_dialog.client_name.text()
            password = start_dialog.client_passwd.text()
            LOGGER.debug(f'Using USERNAME = {name}, PASSWD = {password}.')
        else:
            exit(0)

    LOGGER.info(f'The client is running with the following parameters: server address: '
                f'{server_address} , port: {server_port}, user name: {name}')

    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    database = ClientDatabase(name)

    try:
        transport = ClientTransport(server_port, server_address, 
                                    database, name, password, keys)
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, 'Server error', error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    # Сreating GUI
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {name}')
    client_gui.exec_()

    transport.transport_shutdown()
    transport.join()


if __name__ == '__main__':
    main()
