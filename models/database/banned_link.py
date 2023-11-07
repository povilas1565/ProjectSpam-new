from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column, TEXT, JSON
import enum


class BannedLink(SQLModel, table=True):
    __tablename__ = "banned_groups"

    id: Optional[int] = Field(default=None, primary_key=True)

    url: str = Field(sa_column=Column(TEXT))
    account_id: int
    reason: str = Field(sa_column=Column(TEXT))

    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
