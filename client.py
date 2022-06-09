from dataclasses import dataclass
import sys
import logging
import logs.config_client_log

from PyQt5.QtWidgets import QApplication

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
    server_address, server_port, name = create_parser(LOGGER)

    client_gui = QApplication(sys.argv)

    if not name:
        start_dialog = UserNameDialog()
        client_gui.exec_()
        if start_dialog.ok_pressed:
            name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    LOGGER.info(f'The client is running with the following parameters: server address: '
                f'{server_address} , port: {server_port}, user name: {name}')

    database = ClientDatabase(name)

    try:
        transport = ClientTransport(server_port, server_address, database, name)
    except ServerError as error:
        print(error.text)
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
