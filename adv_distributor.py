import asyncio

import common_tools
from models.database import AdvertisementItem
from pydantic import BaseModel
from store.accounts_store import AccountsStore
import settings
from loguru import logger
import asyncio
import enum
from telegram_chat_logger import TelegramChatLogger


class AdvRunItemStatus(int, enum.Enum):
    NOT_RUNNING = 0
    RUNNING = 1
    NOT_ENOUGH_ACCOUNT = 2
    LINKS_NOT_FOUND = 3


class AdvRunItemInfo(BaseModel):
    account_id: int = -1
    status: AdvRunItemStatus
    adv_item: AdvertisementItem


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class AdvDistributor(metaclass=Singleton):

    def __init__(self):
        self.store = AccountsStore(max_login_accounts=1)
        self.run_items_info = {}

    async def on_ad_added(self, item: AdvertisementItem) -> bool:
        self.run_items_info[int(item.id)] = AdvRunItemInfo(status=AdvRunItemStatus.NOT_RUNNING, adv_item=item)
        return True

    async def on_ad_removed(self, item_id) -> bool:
        try:
            del self.run_items_info[int(item_id)]
        except Exception as e:
            logger.warning(f"Cannot delete ad with id: {id}: {e}")
        return True

    async def _send_message_by_item(self, recipient, item: AdvRunItemInfo):

        logger.info(f"Working with {item}")

        account = await self.store.get_account(item.account_id)

        try:
            await account.follow_to(recipient)
            await asyncio.sleep(5)
        except Exception as e:
            logger.warning(e)

        try:
            await account.send_message_to(recipient, item.adv_item.text, item.adv_item.photos)
            
        except Exception as e:
            logger.warning(e)
            await TelegramChatLogger.send_message_to_chat(
                message=f"❌❌ Не можем отправить сообщение пользователю {recipient}: {e}")

    async def run(self):
        while True:

            logger.info(f"Items list: {list(self.run_items_info)}")
            logger.info(f"Accounts list: {await self.store.get_accounts()}")

            lines = common_tools.read_file(settings.LINKS_PATH)
            wait_result = 25

            for i, x in enumerate(list(self.run_items_info)):
                accounts = await self.store.get_accounts()
                try:
                    account = common_tools.get_index_default(accounts, i)

                    res_item = self.run_items_info[x]

                    if account is not None:

                        res_item.account_id = account

                        if len(lines) > 0:
                            res_item.status = AdvRunItemStatus.RUNNING
                            for link in lines:

                                new_status = self.run_items_info.get(x)

                                if new_status is not None:
                                    if not new_status.adv_item.is_paused:
                                        await self._send_message_by_item(link, res_item)
                                        await asyncio.sleep(settings.DELAY_BETWEEN_LINKS)
                                    else:
                                        logger.info(f"Ad with id {x} is paused, skip")
                                        await self.on_ad_removed(x)
                                        await asyncio.sleep(0.01)
                                else:
                                    logger.info(f"Ad with id {x} was deleted, skip")
                                    await self.on_ad_removed(x)
                                    await asyncio.sleep(0.01)

                        else:
                            res_item.status = AdvRunItemStatus.LINKS_NOT_FOUND
                            await TelegramChatLogger.send_message_to_chat(
                                message=f"❌❌ Не можем отправить объявление {res_item.adv_item.name}: список ссылок не найден")

                        wait_result = len(lines) / settings.DELAY_BETWEEN_LINKS

                    else:
                        res_item.status = AdvRunItemStatus.NOT_ENOUGH_ACCOUNT

                        await TelegramChatLogger.send_message_to_chat(
                            message=f"❌❌ Не можем отправить объявление {res_item.adv_item.name}: недостаточно аккаунтов")

                        wait_result = 15

                except Exception as e:
                    logger.critical(f"Cannot send with id: {x}: {e}")
                    await TelegramChatLogger.send_message_to_chat(
                        message=f"❌❌ Cannot send with id: {x}: {e}")
                
                if wait_result < 25:
                    wait_result = 25

                logger.info(f"Waiting for {wait_result}")
                await asyncio.sleep(wait_result)
                
            await asyncio.sleep(5)
