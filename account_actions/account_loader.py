from opentele.exception import *
from opentele.td import TDesktop, Account
from opentele.api import UseCurrentSession
from opentele.tl import TelegramClient
import os
import telethon
import asyncio
from loguru import logger
from pydantic import BaseModel


class AccountLoginResult(BaseModel):
    client: dict = None
    account_path: str = None
    error: str | None


class AccountsLoader:

    def __init__(self, limit: asyncio.Semaphore):
        self._limit = limit

    async def login_to_account(self, account_path):

        tdataFolder = f"{account_path}/tdata"

        result = AccountLoginResult()

        result.account_path = account_path

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

                result.client = client
                result.error = None

            return result

        except OpenTeleException as e:
            result.error = str(e)

        except RuntimeError as e:
            result.error = str(e)

        except telethon.errors.rpcerrorlist.AuthKeyDuplicatedError as e:
            result.error = str(e)

        except Exception as e:

            result.error = str(e)

        return result
