from opentele.exception import *
from opentele.td import TDesktop, Account
from opentele.api import UseCurrentSession
from opentele.tl import TelegramClient
import os
import telethon
import asyncio
from loguru import logger

class AccountsLoader:
    def __init__(self, base_path, load_callback, error_callback, limit: asyncio.Semaphore):
        self._limit = limit
        self._callback = load_callback
        self._error_callback = error_callback
        self._accounts_path = base_path

    async def login_to_account(self, account_path):

        tdataFolder = f"{account_path}/tdata"

        try:

            logger.info(f"Подгружаем tdata {tdataFolder}")
            tdesk = TDesktop(basePath=tdataFolder)
            assert tdesk.isLoaded()

            client = await TelegramClient.FromTDesktop(
                tdesk, session=f"{account_path}\\telethon.session", flag=UseCurrentSession)
                                
            async with self._limit:

                await client.connect()
                
                info = await client.get_me()
                
                await client.PrintSessions()

                client = {"client": client, "id": info.id,
                        "username": info.username, "path": account_path}

            if self._callback:
                await self._callback(account_path, client)

            return client

        except OpenTeleException as e:
            if self._error_callback:
                await self._error_callback(account_path, str(e))

        except RuntimeError as e:
            if self._error_callback:
                await self._error_callback(account_path, str(e))
            
        except telethon.errors.rpcerrorlist.AuthKeyDuplicatedError as e:
            
            if self._error_callback:
                await self._error_callback(account_path, str(e))

        except Exception as e:

            if self._error_callback:
                await self._error_callback(str(tdataFolder), str(e))

        return None