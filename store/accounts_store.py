from account_actions.account_loader import AccountsLoader
import asyncio
from account_actions.telethon_account import TelethonAccount
from loguru import logger

class AccountsStore:
    def __init__(self, max_login_accounts: int, entered_callback, fail_enter_callback) -> None:

        self._limit = asyncio.Semaphore(max_login_accounts)
        self._loader = AccountsLoader("", self._account_entered, self._account_fail, self._limit)
        self._enter_callback = entered_callback
        self._fail_callback = fail_enter_callback
        self._accounts = {}

    async def _account_entered(self, path, client):
        account = TelethonAccount(asyncio.Semaphore(1), client)
        self._accounts[client['id']] = account
        if self._enter_callback:
            await self._enter_callback(path)

    async def _account_fail(self, path, error):
        if self._fail_callback:
            await self._fail_callback(path, error)

    async def add_account(self, paths):
        tasks = [self._loader.login_to_account(path) for path in paths]
        await asyncio.gather(*tasks)

    async def get_account(self, account_id):
        return self._accounts.get(account_id)

    async def unload_accounts(self):
        res = await self.get_accounts()
        for account in res:
            try:
                result = self._accounts[account]
                if result:
                    result['client'].session.close()
                    del self._accounts[account]
            except Exception as e:
                logger.error(f"Error: {e}")
        return True

    async def remove_account(self, account) -> bool:
        try:
            result = self._accounts[account]
            if result:
                result['client'].session.close()
                del self._accounts[account]
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            return False

    async def get_accounts(self):
        return list(self._accounts.keys())

    async def get_accounts_count(self):
        return len(list(self._accounts.keys()))
