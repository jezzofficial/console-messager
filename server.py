import asyncio
import json
import random
import platform
import os
from colorama import Fore, Back
from sqlite import *
import datetime

HOST = "0.0.0.0"
PORT = 7171
WHITELIST_FILE = "whitelist.txt"
MESSAGE_HISTORY_LIMIT = 50

RESET_COLOR = "\033[0m"
COLORS = [
    "\033[91m",  # Красный
    "\033[92m",  # Зеленый
    "\033[93m",  # Желтый
    "\033[94m",  # Синий
    "\033[95m",  # Магента
    "\033[96m",  # Циан
]

WH = Fore.BLACK + Back.WHITE
resetc = Fore.RESET + Back.RESET

message_history = []
clients = {}
user_colors = {}

def clear_screen():
    if platform.system() == "Linux":
        os.system('clear')
    else:
        os.system('cls')

def load_whitelist():
    try:
        with open(WHITELIST_FILE, "r") as file:
            return {line.split(":")[0]: line.split(":")[1].strip() for line in file.readlines()}
    except FileNotFoundError:
        print(f"{Fore.RED}[ERROR/find_FILE]{resetc} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): Файл {WHITELIST_FILE} не найден!")
        return {}

whitelist = load_whitelist()
def get_user_color(username):
    if username not in user_colors:
        user_colors[username] = random.choice(COLORS)
    return user_colors[username]


async def broadcast(message, exclude_writer=None):

    for writer in clients.values():
        if writer != exclude_writer:
            try:
                writer.write(message.encode())
                await writer.drain()
            except Exception as e:
                print(f"{Fore.RED}[ERROR/SERV->CLI] ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):{resetc} Ошибка отправки сообщения клиенту: {e}")


async def handle_client(reader, writer):
    try:
        credentials = (await reader.read(1024)).decode().strip()
        login, password = credentials.split(":")

        if whitelist.get(login) != password:
            writer.write("Доступ запрещен. Неверный логин или пароль.\n".encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            print(Fore.RED + f"[ERROR/CLI->SERV] ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):" + WH + "Неудачная попытка входа." + resetc)

        user_color = get_user_color(login)
        writer.write(f"Welcome to Chat, {user_color}{login}\033[0m!\n".encode())
        await writer.drain()
        await create(login)
        await updatestatus(login, "Online")
        print(Fore.YELLOW + f"[LOG/CLIENT]{resetc} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):{resetc} Пользователь {login + Fore.CYAN} подключился." + resetc)

        clients[login] = writer

        while True:
            message = (await reader.read(1024)).decode()
            if not message:
                break
            if message == "exit":
                if login in clients:
                    del clients[login]
                    await updatestatus(login, "Offline")
                print(Fore.YELLOW + f"[LOG/CLIENT]{resetc} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): Пользователь {login + Fore.RED} отключился." + resetc)

            else:
                message_data = json.loads(message)
                sender = message_data["sender"]
                encrypted_message = message_data["message"]

                # Добавляем цвет отправителя
                formatted_message = json.dumps({
                    "sender": f"{user_colors[sender]}{sender}\033[0m",
                    "message": encrypted_message
                })

                await broadcast(formatted_message, exclude_writer=writer)

    except Exception as e:
        print(f"{Fore.RED}[ERROR/CLIENT]{resetc} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): Ошибка с клиентом: {e}")
    finally:
        if login in clients:
            del clients[login]
            print(Fore.YELLOW + f"[LOG/CLIENT] ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):{resetc} Пользователь {login + Fore.RED} отключился." + resetc)
            await updatestatus(login, "Offline")
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)
    print(f"{WH}[LOG/SERVER] ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): Сервер запущен на {HOST}:{PORT}" + resetc)
    if await db_start() != False:
        print(f'{WH}[LOG/DATABASE] ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): DATABASE connected!' + resetc)
    else:
        print(f'{WH}[LOG/DATABASE] ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): DATABASE{Fore.RED} disconnected...' + resetc)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    clear_screen()
    asyncio.run(main())