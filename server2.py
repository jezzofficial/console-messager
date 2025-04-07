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

message_history = [] # Позже вххвхвхв
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

        try:
            if await checkban(login) == True:
                writer.write(f"code000:{login} is banned!.\n".encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                print(Fore.RED + f"[ERROR/CLI->SERV]{resetc} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):" + Fore.LIGHTYELLOW_EX + f" Попытка входа от забаненного пользователя {login}." + Fore.RESET)

        except Exception:
                print(Fore.RED + f"[ERROR/CLI->SERV]{resetc} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):" + Fore.LIGHTYELLOW_EX + f" Пользователя не существует!" + Fore.RESET)
        if whitelist.get(login) != password:
            writer.write("code404:Доступ запрещен. Неверный логин или пароль.\n".encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            print(Fore.RED + f"[ERROR/CLI->SERV]{resetc} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):" + Fore.LIGHTYELLOW_EX + f" Неудачная попытка входа от {login}." + Fore.RESET)

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

            if message.split(":")[0] == "kick" or message.split(":")[0] == "ban" or message.split(":")[0] == "addadm" or message.split(":")[0] == "removeadm" or message.split(":")[0] == "allmes" or message.split(":")[0] == "unban":
                command = message.split(":")[0]
                if await checkadm(login) == True:
                    target = message.split(":")[1]
                    if command == "kick":
                        if target in clients:
                            target_write = clients[target]
                            target_write.write(f"code002:{target}, you are kicked.\n".encode())
                            await target_write.drain()
                            del clients[target]
                            target_write.close()
                            await updatestatus(target, "Offline")
                            print(f"{Fore.LIGHTCYAN_EX}[LOG/ADMIN]{resetc} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): User {target} kicked from server.")
                            writer.write(f"code001:{target} are kicked from server.\n".encode())
                            await writer.drain()

                        else:
                            writer.write(f"code001:{target} not found.\n".encode())
                            await writer.drain()

                    if command == "ban":
                        if target in clients:
                            target_write = clients[target]
                            target_write.write(f"code002:{target}, you are banned.\n".encode())
                            await target_write.drain()
                            del clients[target]
                            target_write.close()
                            await updatestatus(target, "Offline")
                            await getban(target)
                            print(f"{Fore.LIGHTCYAN_EX}[LOG/ADMIN]{resetc} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): User {target} banned on server.")
                            writer.write(f"code001:{target} are banned on this server.\n".encode())

                        else:
                            writer.write(f"code001:{target} not found.\n".encode())
                            await writer.drain()

                    if command == "unban":
                        if await checkban(target) == True:
                            await rmban(target)
                            print(f"{Fore.LIGHTCYAN_EX}[LOG/ADMIN]{resetc} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): User {target} unbanned on server.")
                            writer.write(f"code001:{target} are unbanned on this server.\n".encode())

                        else:
                            writer.write(f"code001:{target} not found.\n".encode())
                            await writer.drain()

                    if command == "addadm":
                        try:
                            target_write = clients[target]
                            await updateadm(target, "True")
                            print(f"{Fore.LIGHTCYAN_EX}[LOG/ADMIN]{resetc} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): User {target} now is Admin.")
                            target_write.write(f"code001:{target}, you have an admin on this server.\n".encode())
                            writer.write(f"code001:{target} now have an admin.".encode())

                        except Exception:
                            writer.write(f"code001:{target} not found.\n".encode())
                            await writer.drain()

                    if command == "removeadm":
                        try:
                            target_write = clients[target]
                            await updateadm(target, "False")
                            print(f"{Fore.LIGHTCYAN_EX}[LOG/ADMIN]{resetc} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): User {target} now is not Admin.")
                            target_write.write(f"code001:{target}, you have stopped being an admin on this server.\n".encode())
                            writer.write(f"code001:{target} now don't have an admin.".encode())

                        except Exception:
                            writer.write(f"code001:{target} not found.\n".encode())
                            await writer.drain()

                    if command == "allmes":
                        text = "\n"
                        lens = len(clients)
                        while lens != 0:
                            for login in clients:
                                count = await getmes(login)
                                color = get_user_color(login)
                                text = text + f"| {color}{login}\033[0m - {count}\n"
                                lens = lens - 1
                        writer.write(f"code001:{text}".encode())
                        await writer.drain()



                else:
                    writer.write("code001:Access Denied.\n".encode())
                    await writer.drain()
                    print(Fore.RED + f"[ERROR/CLI->SERV]{resetc} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):" + Fore.LIGHTYELLOW_EX + f" Попытка воспользоваться админ. панелью от {login}." + Fore.RESET)



            else:
                message_data = json.loads(message)
                sender = message_data["sender"]
                encrypted_message = message_data["message"]

                # Добавляем цвет отправителя
                formatted_message = json.dumps({
                    "sender": f"{user_colors[sender]}{sender}\033[0m",
                    "message": encrypted_message
                })

                await updatemes(login)
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