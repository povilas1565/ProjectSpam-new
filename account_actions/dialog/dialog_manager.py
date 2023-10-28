from tools import Tools
from loggers.inline_logger import InlineLogger
from account_actions.account_loader import AccountsLoader
from account_actions.telethon_account import TelethonAccount
import asyncio
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.account import UpdateUsernameRequest
from telethon import functions, types
import random
from dataclasses import dataclass
from typing import List
from data_loader.data_loader import DataLoader
import random


@dataclass
class DialogInfo:
    dialog_files: List[str]
    accounts: List[TelethonAccount] = None


class Dialog:
    def __init__(self, info: DialogInfo, dialog_sem: asyncio.Semaphore) -> None:
        self._info = info
        self._data_loader = DataLoader("./")
        self._dialog_data = self._get_dialog_data()
        self._dialog_sem = dialog_sem
        self._logger = InlineLogger("Dialog")
        self._runned = True

    def _get_dialog_data(self):
        data = self._data_loader.load_data(random.choice(self._info.dialog_files))
        return [str(line).rstrip()[3:] for line in data]

    async def _readd_friends(self):

        task = self._info.accounts[0].add_to_contact(
            await self._info.accounts[1].get_username()
        )

        async with self._dialog_sem:
            await self._info.accounts[0].run_task(task)

        await asyncio.sleep(3)

        task = self._info.accounts[1].add_to_contact(
            await self._info.accounts[0].get_username()
        )

        async with self._dialog_sem:
            await self._info.accounts[1].run_task(task)

    async def start(self):

        await self._readd_friends()

        while self._runned:

            self._dialog_data = self._get_dialog_data()

            try:

                for i, line in enumerate(self._dialog_data):

                    if i % 2 == 0:

                        task = self._info.accounts[0].send_message_to(
                            await self._info.accounts[1].get_username(), line
                        )

                        async with self._dialog_sem:
                            await self._info.accounts[0].run_task(task)

                        await asyncio.sleep(1)

                        task = self._info.accounts[1].read_messages(
                            await self._info.accounts[0].get_username(), 1
                        )

                        async with self._dialog_sem:
                            await self._info.accounts[1].run_task(task)

                    else:

                        task = self._info.accounts[1].send_message_to(
                            await self._info.accounts[0].get_username(), line
                        )

                        async with self._dialog_sem:
                            await self._info.accounts[1].run_task(task)

                        await asyncio.sleep(1)

                        task = self._info.accounts[0].read_messages(
                            await self._info.accounts[1].get_username(), 1
                        )

                        async with self._dialog_sem:
                            await self._info.accounts[0].run_task(task)

                    await asyncio.sleep(random.randint(120, 400))
            except Exception as e:
                message = f"Ошибка отправки сообщения: {e}"
                if "as username" in str(e):
                    message += (
                        f"\nВнимание! Ошибка отлета аккаунта. Останавливаем диалог"
                    )
                    await self._logger.send_error(f"{message}")
                    self._runned = False
                    break
