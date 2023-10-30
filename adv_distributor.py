import asyncio

import common_tools
from models.database import AdvertisementItem
from pydantic import BaseModel
from store.accounts_store import AccountsStore
import settings
from loguru import logger
import asyncio
import enum
from collections import deque

class AdvRunItemStatus(int, enum.Enum):
    NOT_RUNNING = 0
    IN_QUEUE = 1
    NOT_ENOUGHT_ACCOUNT = 2
    RUNNING = 3

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
        return self.run_items_info
    
    async def on_ad_removed(self, item_id) -> bool:
        del self.run_items_info[item_id]
        return True
    
    async def run(self):
        while True:
            for key, value in self.run_items_info.items():
                print(key, value)
                await asyncio.sleep(3)
    