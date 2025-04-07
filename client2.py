import asyncio
import base64
import datetime
import json
import os
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.formatted_text import ANSI
import colorama
import platform
from config import *
from Crypto.Cipher import AES
from colorama import Fore, Back

HOST = "212.20.54.190"
PORT = 7171

key_base64 = "UE0Rsx3yTq2gV5U92NeoVzzlbQavkhH3VgPVLgimyk4="
key = base64.b64decode(key_base64)
def clear_screen():
    if platform.system() == "Linux":
        os.system('clear')
    else:
        os.system('cls')


async def encrypt_mes(mes):
    cipher = AES.new(key, AES.MODE_GCM)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(mes.encode())

    encrypt_data = {
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "tag": base64.b64encode(tag).decode()
    }

    return encrypt_data

async def decrypt_mes(mes: dict) -> str:
    nonce = base64.b64decode(mes["nonce"])
    ciphertext = base64.b64decode(mes["ciphertext"])
    tag = base64.b64decode(mes["tag"])

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    decrypt_message = cipher.decrypt_and_verify(ciphertext, tag)
    return decrypt_message.decode()

async def receive_messages(reader):
    while True:
        try:
            message = (await reader.read(1024)).decode()
            now = datetime.datetime.now().strftime('%m-%d %H:%M')
            if message.split(':')[0] == "code002":
                print_formatted_text(ANSI(f"[NOTIFY/SERVER] ({now}): {message.split(':')[1]}"))
                exit()

            if message.split(':')[0] == "code001":
                print_formatted_text(ANSI(f"[NOTIFY/SERVER]] ({now}): {message.split(':')[1]}"))

            if message:
                mes_data = json.loads(message)
                sender = mes_data["sender"]
                encrp_mes = mes_data["message"]
                decr_mes = await decrypt_mes(encrp_mes)
                print_formatted_text(ANSI(f"[{sender}] ({now}): {decr_mes}"))
        except Exception as e:
            print_formatted_text(f"Ошибка при получении сообщений: {e}")
            pass


async def send_messages(writer, session, login):
    while True:
        try:
            message = await session.prompt_async(f"[{login}]: ")
            if message == "exit":
                writer.write("exit".encode())
                await writer.drain()
                print_formatted_text("Вы отключились от сервера.")
                exit()

            if message.split(':')[0] == 'kick':
                writer.write(message.encode())
                await writer.drain()

            if message.split(':')[0] == 'ban':
                writer.write(message.encode())
                await writer.drain()

            if message.split(':')[0] == 'unban':
                writer.write(message.encode())
                await writer.drain()

            if message.split(':')[0] == 'addadm':
                writer.write(message.encode())
                await writer.drain()

            if message.split(':')[0] == 'removeadm':
                writer.write(message.encode())
                await writer.drain()

            if message.split(':')[0] == 'allmes':
                writer.write(message.encode())
                await writer.drain()

            encrp_mes = await encrypt_mes(message)
            mes_data = {
                "sender": login,
                "message": encrp_mes
            }
            writer.write(json.dumps(mes_data).encode())
            await writer.drain()

        except EOFError:
            print_formatted_text("Отключение...")
            break
        except KeyboardInterrupt:
            print_formatted_text("Принудительное завершение.")
            break


async def main():
    reader, writer = await asyncio.open_connection(HOST, PORT)

    login = input(Fore.BLACK + Back.WHITE + "Login: ")
    password = input(Fore.BLACK + Back.WHITE + "Password: ")
    writer.write(f"{login}:{password}".encode())
    await writer.drain()
    response = (await reader.read(1024)).decode()

    if response.split(":")[0] == 'code404':
        print_formatted_text(f"[SERVER] ({datetime.datetime.now().strftime('%m-%d %H:%M')}): {response.split(":")[1]}")
        exit()

    if response.split(":")[0] == 'code000':
        print_formatted_text(f"[SERVER] ({datetime.datetime.now().strftime('%m-%d %H:%M')}): {response.split(":")[1]}")
        exit()

    print(response)

    session = PromptSession()

    asyncio.create_task(receive_messages(reader))

    with patch_stdout():
        try:
            await send_messages(writer, session, login)
        except KeyboardInterrupt:
            print_formatted_text("\nОтключение от сервера.")
            writer.write("exit".encode())
            await writer.drain()
            exit()


if __name__ == "__main__":
    clear_screen()
    asyncio.run(main())