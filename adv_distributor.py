import asyncio
import random
import time
import common_tools
from models.database import AdvertisementItem
from pydantic import BaseModel
from store.accounts_store import AccountsStore
import settings
from loguru import logger
import asyncio
import enum
from telegram_chat_logger import TelegramChatLogger
import time_manager
from advertisement_manager import AdvertisementManager


class AdvRunItemStatus(int, enum.Enum):
    NOT_RUNNING = 0
    RUNNING = 1
    NOT_ENOUGH_ACCOUNT = 2
    LINKS_NOT_FOUND = 3
    WAITING_FOR_TIME = 4


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
        self._semaphore = asyncio.Semaphore(1)
        self._adv_manager = AdvertisementManager()

    async def on_ad_added(self, item: AdvertisementItem) -> bool:
        self.run_items_info[int(item.id)] = AdvRunItemInfo(status=AdvRunItemStatus.NOT_RUNNING, adv_item=item)
        return True

    async def on_ad_removed(self, item_id) -> bool:
        try:
            del self.run_items_info[int(item_id)]
        except Exception as e:
            logger.warning(f"Cannot delete ad with id: {id}: {e}")
        return True

    async def _send_message_by_item(self, recipient, item: AdvRunItemInfo) -> bool:

        logger.info(f"Working with {item}")

        account = await self.store.get_account(item.account_id)

        if account is not None:

            item.status = AdvRunItemStatus.RUNNING

            async with self._semaphore:
                try:
                    await account.follow_to(recipient)
                    await asyncio.sleep(5)
                except Exception as e:
                    logger.warning(e)

                try:
                    await account.send_message_to(recipient, item.adv_item.text, item.adv_item.photos)

                    return True

                except Exception as e:
                    logger.warning(e)
                    await TelegramChatLogger.send_message_to_chat(
                        message=f"❌❌ Не можем отправить сообщение пользователю {recipient}: {e}")

                await asyncio.sleep(random.randint(10, 20))

        else:

            item.status = AdvRunItemStatus.NOT_ENOUGH_ACCOUNT

            await TelegramChatLogger.send_message_to_chat(
                message=f"❌❌ Не можем отправить сообщение пользователю {recipient}. Account is none")

        return False

    async def _run_for_link(self, link, item: AdvRunItemInfo):

        item.adv_item = self._adv_manager.update_item_info(item.adv_item.id)

        if item.adv_item.publish_time is not None:
            if await time_manager.get_current_hour() == item.adv_item.publish_time:
                if not item.adv_item.was_sent:
                    if await self._send_message_by_item(link, item):
                        item.adv_item.was_sent = True
                        self._adv_manager.refresh_item(item.adv_item)
            else:
                if item.adv_item.was_sent:
                    item.adv_item.was_sent = False
                    self._adv_manager.refresh_item(item.adv_item)
        else:
            await self._send_message_by_item(link, item)

    async def run(self):
        while True:

            logger.info(f"Items list: {list(self.run_items_info)}")
            logger.info(f"Accounts list: {await self.store.get_accounts()}")

            lines = common_tools.read_file(settings.LINKS_PATH)

            accounts = await self.store.get_accounts()

            if len(lines) > 0 and len(accounts) > 0:

                accounts = await self.store.get_accounts()

                for i, x in enumerate(list(self.run_items_info)):

                    account = common_tools.get_index_default(accounts, i)

                    res_item = self.run_items_info[x]

                    res_item.account_id = account

                    diff = time.time() - res_item.adv_item.last_sent_time_ms

                    if res_item.adv_item.publish_time is None:
                        diff_val = settings.DELAY_BETWEEN_LINKS if settings.DELAY_BETWEEN_LINKS > settings.MIN_DELAY else settings.MIN_DELAY
                    else:
                        diff_val = 30

                    if diff > diff_val:

                        for link in lines:
                            asyncio.create_task(self._run_for_link(link, res_item))

                        adv = self._adv_manager.update_item_info(res_item.adv_item.id)
                        adv.last_sent_time_ms = time.time()
                        self._adv_manager.refresh_item(adv)
                    else:
                        logger.info(f"Таска была отправлена {diff} секунд назад, а надо {diff_val}")

            await asyncio.sleep(5)
