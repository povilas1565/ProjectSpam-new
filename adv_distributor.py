import asyncio

import common_tools
from models.database import AdvertisementItem
from pydantic import BaseModel
from store.accounts_store import AccountsStore
from account_actions.telethon_account import TelethonAccount
import settings
from advertisement_manager import AdvertisementManager
from loguru import logger
import asyncio
from collections import deque


class AdvRunItem(BaseModel):
    account_id: int
    status: bool
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

        self._adv_manager = AdvertisementManager()

        self.ad_status = {}
        self._free_accounts = deque()

    async def _on_account_loaded(self):
        res = await self.store.get_accounts()
        self._free_accounts.append(res[-1])

    async def on_ad_added(self, item: AdvertisementItem):
        account_id = self._free_accounts.pop()

        if account_id is None:
            logger.critical(f"Cannot attach account is {account_id}")
        else:
            m = AdvRunItem(account_id=account_id,
                           status=True,
                           adv_item=item)

            self.ad_status[int(m.adv_item.id)] = True

            asyncio.create_task(self._run_for_account(m))

    async def on_ad_removed(self, item_id):
        logger.info(f"Set {item_id} to false")
        self.ad_status[int(item_id)] = False
    
    async def unload_accounts(self):
        await self.store.unload_accounts()

    async def reset(self):
        await self.store.unload_accounts()
        self._free_accounts.clear()
        for key, value in self.ad_status.keys():
            self.ad_status[key] = False


    async def reload(self):
        await self.store.unload_accounts()
        res = common_tools.get_files_in_dir(f'{settings.ACCOUNTS_PATH}/ready')
        results = await self.store.add_account(res)
        for result in results:
            if result.error is None:
                await self._on_account_loaded()

    async def add_account(self, path):
        results = await self.store.add_account(path)
        for result in results:
            if result.error is None:
                await self._on_account_loaded()
        return results

    async def _run_for_account(self, item: AdvRunItem):
        
        while True:
            lines = common_tools.read_file(settings.LINKS_PATH)

            for line in lines:

                res = self.ad_status[int(item.adv_item.id)]

                logger.info(f"Working on {int(item.adv_item.id)} ad, status: {res}")

                if not res:
                    logger.success(f"Account id: {item.account_id} is stopped")
                    self._free_accounts.append(item.account_id)
                    return

                account = await self.store.get_account(item.account_id)

                try:
                    await account.follow_to(line)
                    await asyncio.sleep(5)
                except Exception as e:
                    logger.warning(e)

                try:
                    await account.send_message_to(line, item.adv_item.text, item.adv_item.photos)
                except Exception as e:
                    logger.warning(e)

                await asyncio.sleep(settings.DELAYS_BETWEEN_CHANNELS)

            await asyncio.sleep(settings.DELAYS_IN_CHANNEL)

    async def run(self):
        items = self._adv_manager.get_all_advertisement()

        for item in items:

            try:
                account_id = self._free_accounts.pop()
            except Exception as e:
                account_id = None

            if account_id is None:
                logger.critical(f"Cannot attach account is {account_id}")
            else:
                m = AdvRunItem(account_id=account_id,
                               status=True,
                               adv_item=item)

                self.ad_status[int(m.adv_item.id)] = True

                asyncio.create_task(self._run_for_account(m))