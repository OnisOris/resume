from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Timestamped(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()


class WishItemBase(SQLModel):
    title: str
    description: str | None = Field(default=None)
    link: str | None = Field(default=None)
    price: str | None = Field(default=None)


class WishItem(WishItemBase, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reserved_by: str | None = Field(default=None)
    reserved_contact: str | None = Field(default=None)
    reserved_note: str | None = Field(default=None)
    reserved_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    image_path: str | None = Field(default=None, description="Относительный путь к файлу с изображением")


class PostBase(SQLModel):
    title: str
    summary: str
    body: str
    tags: str | None = Field(default=None, description="CSV список тегов")


class Post(PostBase, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
