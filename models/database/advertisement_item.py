from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column, TEXT, JSON
import enum


class AdvertisementItem(SQLModel, table=True):
    __tablename__ = "advertisement_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    photos: List[str] = Field(sa_column=Column(JSON), default=None)
    text: str = Field(sa_column=Column(TEXT), default=None)
    name: str = Field(sa_column=Column(TEXT))

    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
