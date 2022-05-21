import imp
import logging
import ipaddress

LOGGER = logging.getLogger('server')


class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            LOGGER.critical(
                f'The port must be specified in the range from 1024 to 65535')
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class Addr:
    def __set__(self, instans, value):
        if value:
            try:
                if value == 'localhost':
                    value = '127.0.0.1'
                ip = ipaddress.ip_address(value)
            except ValueError as e:
                LOGGER.critical(f'The IP address is entered incorrectly {e}')
                exit(1)
        instans.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
