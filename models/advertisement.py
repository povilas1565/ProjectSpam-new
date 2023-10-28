import enum
from pydantic import BaseModel
from models.database.advertisement_item import AdvertisementItem


class AdvertisementCreateStatus(int, enum.Enum):
    ALREADY_EXIST = 0
    CREATED = 1
    FAILED = 2


class AdvertisementCreateResult(BaseModel):
    status: AdvertisementCreateStatus = None
    item: AdvertisementItem = None
