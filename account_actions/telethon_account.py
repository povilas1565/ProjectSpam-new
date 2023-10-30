from .account import Account
from telethon.tl.functions.channels import JoinChannelRequest
import asyncio
from telethon import functions, types
import names
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.account import UpdateUsernameRequest
from telethon.tl.functions.channels import LeaveChannelRequest
from loguru import logger
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact

class TelethonAccount(Account):

    def __init__(self, task_limit: asyncio.Semaphore, client) -> None:
        super().__init__(task_limit)
        self._client = client
        self._entities = {}
        
    async def run_task(self, wrapped_func):
        async with self._task_limit:

            res = await self._client['client'](functions.account.UpdateStatusRequest(
                offline=False
            ))

            res = await wrapped_func

            await asyncio.sleep(2)

            return res

    async def search(self, link) -> bool:
        res = await self._client['client'](functions.contacts.SearchRequest(
            q=link,
            limit=59
        ))

        for res_chat in res.chats:
            print(res_chat.username)
            if res_chat.username in link:
                return True

        return False

    async def follow_to(self, url) -> bool:

        entity = await self._client['client'].get_entity(url)
        
        if entity:
            res = await self._client['client'](JoinChannelRequest(url))
            logger.info(f"followed to {url}")
            return res.chats[0].id
        else:
            logger.error(
                f"cannot follow to {url}. Entity is {entity}")
        return None

    async def unfollow_from(self, chat_id):
        return await self._client['client'].delete_dialog(chat_id)

    async def send_message_to(self, receiver, text, file=None):

        for i in range(int(len(text) / 2)):
            result = await self._client['client'](functions.messages.SetTypingRequest(
                peer=receiver,
                action=types.SendMessageTypingAction()
            ))

            await asyncio.sleep(int(len(text) * 0.00001))

        result = await self._client['client'](functions.messages.SetTypingRequest(
            peer=receiver,
            action=types.SendMessageCancelAction()
        ))

        entity = None

        if not self._entities.get("message"):
            entity = await self._client['client'].get_input_entity(receiver)
            self._entities['message'] = {
                'receiver': receiver, 'entity': entity}
        else:
            if self._entities['message']['receiver'] in receiver:
                entity = self._entities['message']['entity']
            else:
                entity = await self._client['client'].get_input_entity(receiver)

                self._entities['message'] = {
                    'receiver': receiver, 'entity': entity}

        if entity:
            await self._client['client'].send_message(entity=entity, message=text, file=file)
        else:
            logger.error(
                f"cannot send message to {receiver}. Entity is: {entity}")
            raise Exception("cannot send message to {receiver}. Entity is: {entity}")

    async def get_follows(self):
        print("get follows")

    async def get_id(self):
        return self._client['id']

    async def get_username(self):
        return self._client['username']

    async def read_messages(self, login, limit):

        entity = None

        if not self._entities.get("message"):
            entity = await self._client['client'].get_input_entity(login)
            self._entities['message'] = {
                'receiver': login, 'entity': entity}
        else:
            if self._entities['message']['receiver'] in login:
                entity = self._entities['message']['entity']
            else:
                entity = await self._client['client'].get_input_entity(login)

                self._entities['message'] = {
                    'receiver': login, 'entity': entity}

        if entity:
            for message in await self._client['client'].get_messages(entity, limit=limit):
                await self._client['client'].send_read_acknowledge(entity, message)
                await asyncio.sleep(0.02)
        else:
            logger.error(
                f"cannot read messages from {login}. Entity is {entity}")

    def stop(self):
        del self
        
    async def import_contact_by_phone_number(self, phone_number):
        contact = InputPhoneContact(client_id=0, phone=phone_number, first_name=names.get_first_name(), last_name=names.get_last_name())
        return await self._client['client'](ImportContactsRequest([contact]))

    async def add_to_contact(self, target_username) -> bool:

        res = await self._client['client'](functions.contacts.GetContactsRequest(hash=0))

        if res:

            if not any(u.username == target_username for u in res.users):

                result = await self._client['client'](functions.contacts.AddContactRequest(
                    id=target_username,
                    first_name=names.get_first_name(),
                    last_name=names.get_last_name(),
                    phone='',
                    add_phone_privacy_exception=True
                ))

                logger.info(f"added {target_username} as friend")
            else:
                logger.info(f"username {target_username} is friend now")

        return True

    def get_api(self):
        return self._client

    async def set_username(self, account_username):
        res = await self._client['client'](UpdateUsernameRequest(account_username))
        self.get_api()['username'] = account_username
        return res

    async def set_bio(self, bio):
        res = await self._client['client'](UpdateProfileRequest(
            about=bio
        ))
        return res

    async def get_dialogs(self):
        dialogs = []
        async for dialog in self._client['client'].iter_dialogs():
            dialogs.append(dialog.entity.id)
        return dialogs
