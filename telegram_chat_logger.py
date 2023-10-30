import common_tools
import settings
from loguru import logger


class TelegramChatLogger:
    @staticmethod
    def _get_url(chat_id, message):
        return f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage?chat_id={chat_id}&text={message}"

    @staticmethod
    async def send_message_to_chat(message: str, chat_id=None):
        try:
            if chat_id is None:
                for chat_id in settings.ALLOWED_CHATS:
                    await common_tools.make_get_request(TelegramChatLogger._get_url(chat_id, message))
            else:
                await common_tools.make_get_request(TelegramChatLogger._get_url(chat_id, message))
        except Exception as e:
            logger.critical(f"Cannot send {message=} to {chat_id=}: {e}")
