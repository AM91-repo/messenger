import subprocess
import os
import signal
from sys import platform
import time


def run_client(process):
    if platform == 'linux':
        process.append(subprocess.Popen(
            f'gnome-terminal -- bash -c "python3 client.py -n test{i + 1}"', shell=True, preexec_fn=os.setpgrp))
    elif platform == 'win32':
        process.append(subprocess.Popen(
            f'python client.py -n test{i + 1}', creationflags=subprocess.CREATE_NEW_CONSOLE))


def run_server(process):
    if platform == 'linux':
        process.append(subprocess.Popen(
            'gnome-terminal -- bash -c "python3 server.py"', shell=True,  preexec_fn=os.setpgrp))
    elif platform == 'win32':
        process.append(subprocess.Popen('python server.py',
                                        creationflags=subprocess.CREATE_NEW_CONSOLE))


d = os.getcwd()
print(platform)

process = []

while True:
    action = input(
        'Выберите действие: q - выход , s - запустить сервер и клиенты, x - закрыть все окна:')

    if action == 'q':
        break
    elif action == 's':
        clients_count = int(
            input('Введите количество тестовых клиентов для запуска: '))

        run_server(process)

        for i in range(clients_count):
            time.sleep(1)
            run_client(process)
            print(f'Запущен клиент test{i + 1}')

        print(process)
    elif action == 'x':
        while process:
            process.pop().kill()
