import asyncio
import os
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.formatted_text import ANSI 
import colorama
import platform

HOST = "0.0.0.0" 
PORT = 7171

def clear_screen():
    if platform.system() == "Linux":
        os.system('clear')
    else:
        os.system('cls')


async def receive_messages(reader):
    while True:
        try:
            message = (await reader.read(1024)).decode().strip()
            if message:
                print_formatted_text(ANSI(message))
        except Exception as e:
            print_formatted_text(f"Ошибка при получении сообщений: {e}")
            break


async def send_messages(writer, session, login):
    while True:
        try:
            message = await session.prompt_async(f"[{login}]: ")
            if message == "exit":
                writer.write("exit".encode())
                await writer.drain()
                print_formatted_text("Вы отключились от сервера.")
                exit()
            writer.write(message.encode())
            await writer.drain()
        except EOFError:
            print_formatted_text("Отключение...")
            break
        except KeyboardInterrupt:
            print_formatted_text("Принудительное завершение.")
            break


async def main():
    reader, writer = await asyncio.open_connection(HOST, PORT)

    login_prompt = (await reader.read(1024)).decode()
    login = input(login_prompt)
    writer.write(login.encode())
    await writer.drain()

    password_prompt = (await reader.read(1024)).decode()
    password = input(password_prompt)
    writer.write(password.encode())
    await writer.drain()

    session = PromptSession()

    asyncio.create_task(receive_messages(reader))

    with patch_stdout():
        try:
            await send_messages(writer, session, login)
        except KeyboardInterrupt:
            print_formatted_text("\nОтключение от сервера.")
            writer.close()
            await writer.wait_closed()


if __name__ == "__main__":
    clear_screen()
    asyncio.run(main())