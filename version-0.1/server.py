import asyncio
import random
import platform
import os
from colorama import Fore, Back

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

WH = Fore.BLACK + Fore.WHITE
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
        print(f"Файл {WHITELIST_FILE} не найден!")
        return {}


def get_user_color(username):
    if username not in user_colors:
        user_colors[username] = random.choice(COLORS)
    return user_colors[username]


async def broadcast(message, exclude_writer=None):
    disconnected_clients = []

    for login, writer in clients.items():
        if writer != exclude_writer:
            try:
                writer.write((message + "\n").encode())
                await writer.drain()
            except Exception as e:
                print(f"{Fore.RED}[ERROR/SERVCLI]{resetc} Ошибка отправки сообщения клиенту {login}: {e}")
                disconnected_clients.append(login)

    for login in disconnected_clients:
        del clients[login]


async def handle_client(reader, writer):
    global message_history
    whitelist = load_whitelist()

    try:
        writer.write("Введите логин: ".encode())
        await writer.drain()
        login = (await reader.read(1024)).decode().strip()

        writer.write("Введите пароль: ".encode())
        await writer.drain()
        password = (await reader.read(1024)).decode().strip()

        if login in whitelist and whitelist[login] == password:
            writer.write("Добро пожаловать в чат!\n".encode())
            await writer.drain()
            print(Fore.YELLOW + f"[LOG/CLIENT] Пользователь {login + Fore.CYAN} подключился." + resetc)

            for msg in message_history:
                writer.write((msg + "\n").encode())
                await writer.drain()

            clients[login] = writer

            user_color = get_user_color(login)

            while True:
                message = (await reader.read(1024)).decode().strip()
                if not message:
                    break
                if message == "exit":
                    if login in clients:
                        del clients[login]
                    print(Fore.YELLOW + f"[LOG/CLIENT]{resetc} Пользователь {login + Fore.RED} отключился." + resetc)
                else:
                    lenm = len(message)
                    formatted_message = f"{user_color}[{login}]{RESET_COLOR}: {message}"
                    formatted_messageforconsole = f"{user_color}[{login}]{RESET_COLOR}: {lenm*"x"}"
                    print(formatted_messageforconsole)

                message_history.append(formatted_message)
                if len(message_history) > MESSAGE_HISTORY_LIMIT:
                    message_history.pop(0)

                await broadcast(formatted_message, exclude_writer=writer)
        else:
            writer.write("Неверный логин или пароль. Соединение закрыто.".encode())
            await writer.drain()
            print(Fore.RED + "[ERROR/CLIENT] " + WH + "Неудачная попытка входа." + resetc)
    except Exception as e:
        print(f"Ошибка с клиентом: {e}")
    finally:
        if login in clients:
            del clients[login]
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)
    print(f"{WH}[LOG/SERVER] Сервер запущен на {HOST}:{PORT}" + resetc)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    clear_screen()
    asyncio.run(main())