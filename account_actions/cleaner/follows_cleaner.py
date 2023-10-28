from ..account_data_manager import AccountDataManager
from service.redis_service import RedisSerivce
from ..telethon_account import TelethonAccount
import asyncio
from loggers.inline_logger import InlineLogger
import random

class FollowsCleaner:
    def __init__(self, service: RedisSerivce, limit: asyncio.Semaphore) -> None:
        self._data_manager = AccountDataManager(service)
        self._limit = limit
        self._logger = InlineLogger("Account cleaner")
    
    async def clear_follows(self, account: TelethonAccount, decrease_to, delay_between_unfollow):

        follows = await self._data_manager.get_account_follows(await account.get_id())

        while follows > decrease_to:

            try:

                oldest_follow = await self._data_manager.get_first_follow(await account.get_id())

                async with self._limit:
                    
                    print(f"Oldest follow is {oldest_follow} and chatid: {oldest_follow['chat_id']}")

                    await account.unfollow_from(oldest_follow['url'])

                await self._logger.send_info(f"На аккаунте {await account.get_id()}: {follows} подписок из {decrease_to} максимально возможных. Отписали аккаунт от группы {oldest_follow['url']}")

                follows = await self._data_manager.get_account_follows(await account.get_id())

                await asyncio.sleep(delay_between_unfollow)
            except Exception as e:
                await self._logger.send_error(f"Ошибка отписки аккаунта: {e}")

    async def keep_account_follows(self, account: TelethonAccount, max_follows, delay_between_unfollow):
        await asyncio.sleep(random.randint(5, 150))
        while True:
            await self.clear_follows(account, max_follows, delay_between_unfollow)
            await asyncio.sleep(600)
