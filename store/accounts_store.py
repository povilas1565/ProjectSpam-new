from account_actions.account_loader import AccountsLoader
import asyncio
from account_actions.telethon_account import TelethonAccount
from loguru import logger

class AccountsStore:
    def __init__(self, max_login_accounts: int = 1) -> None:

        self._limit = asyncio.Semaphore(max_login_accounts)
        self._loader = AccountsLoader(self._limit)
        self._accounts = {}

    async def add_account(self, paths):
        tasks = [self._loader.login_to_account(path) for path in paths]
        results = await asyncio.gather(*tasks)
        for result in results:
            if result.error is None:
                account = TelethonAccount(asyncio.Semaphore(1), result.client)
                self._accounts[result.client['id']] = account
        return results

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
