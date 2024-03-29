import time
from typing import List
from models.database import AdvertisementItem
from database_manager import DatabaseManager
from loguru import logger
from models import *
import shutil
import settings

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class AdvertisementManager(metaclass=Singleton):
    def __init__(self):
        self._last_message_time = time.time()
        self._database_manager = DatabaseManager()

    def create_advertisement(self, name: str, text: str, photos: List[str], publish_time) -> AdvertisementCreateResult:
        item = AdvertisementItem(name=name, text=text, photos=photos, publish_time=publish_time)

        if self._database_manager.is_exist(AdvertisementItem, AdvertisementItem.name == name):
            logger.warning(f"Реклама с именем {name} уже существует")
            status = AdvertisementCreateStatus.ALREADY_EXIST
        else:
            self._database_manager.save_data(item)
            logger.success(f"Реклама с именем {name} сохранена")
            status = AdvertisementCreateStatus.CREATED

        result = AdvertisementCreateResult(status=status, item=item)

        return result

    def update_item_info(self, id) -> AdvertisementItem:
        try:
            return self._database_manager.read_data(AdvertisementItem, AdvertisementItem.id == id)
        except Exception as e:
            logger.warning(f"Cannot update item info: {e}")
            return None
        
    def refresh_item(self, item) -> AdvertisementItem:
        try:
            return self._database_manager.save_data(item)
        except Exception as e:
            logger.warning(f"Cannot refresh item info: {e}")
            return None
        
    def get_all_advertisement(self) -> List[AdvertisementItem]:
        return self._database_manager.read_data(AdvertisementItem)
    
    def remove_ad(self, id) -> bool:
        try:
            result = self._database_manager.remove_data(AdvertisementItem, AdvertisementItem.id == id)
        
            pth = f"{settings.PHOTOS_PATH}/{result.name}"
            
            logger.info(f"Removing {pth}")

            try:
                for i in range(0, 5):
                    shutil.rmtree(pth)
                    break
            except Exception as e:
                logger.warning(f"Cannot delete {pth}")

            logger.success(f"Реклама с id {id} удалена")
            return True
        except Exception as e:
            logger.error(f"Не можем удалить рекламу с id {id}. Причина: {e}")
        return False

    def get_ad_info(self, id) -> AdvertisementItem:
        try:
            result = self._database_manager.read_data(AdvertisementItem, AdvertisementItem.id == id)
            return result
        except Exception as e:
            logger.error(f"Не можем получить информацию о рекламе с id {id}. Причина: {e}")
        return None

    def pause_unpause_ad(self, id) -> AdvertisementItem:
        try:
            result = self._database_manager.read_data(AdvertisementItem, AdvertisementItem.id == id)

            result.is_paused = not result.is_paused

            self._database_manager.save_data(result)

            return result
        except Exception as e:
            logger.error(f"Не можем поставить рекламу с id {id}. Причина: {e}")
        return None

    def change_ad_publish_time(self, id, new_time) -> AdvertisementItem:
        try:
            result = self._database_manager.read_data(AdvertisementItem, AdvertisementItem.id == id)

            result.publish_time = new_time

            self._database_manager.save_data(result)

            return result
        except Exception as e:
            logger.error(f"Не можем изменить время публикации рекламы с id {id}. Причина: {e}")
        return None

