import asyncio
from telegram_chat_logger import TelegramChatLogger

async def main():
    await TelegramChatLogger.send_message_to_chat("hello")

asyncio.run(main())