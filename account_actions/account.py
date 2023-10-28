from abc import ABC, abstractmethod
import asyncio


class Account(ABC):

    def __init__(self, task_limit: asyncio.Semaphore):
        self._task_limit = task_limit

    @abstractmethod
    async def follow_to(self, url):
        pass

    @abstractmethod
    async def unfollow_from(self, url):
        pass

    @abstractmethod
    async def send_message_to(self, url):
        pass

    @abstractmethod
    async def get_follows(self):
        pass

    @abstractmethod
    async def get_id(self):
        pass

    @abstractmethod
    async def get_username(self):
        pass

    @abstractmethod
    async def add_to_contact(self, target_username):
        pass
