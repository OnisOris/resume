from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class WishItemCreate(BaseModel):
    title: str
    description: str | None = None
    link: str | None = None
    price: str | None = None
    image_path: str | None = None


class WishItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    link: str | None = None
    price: str | None = None
    image_path: str | None = None


class WishItemReserve(BaseModel):
    name: str = Field(..., description="Имя бронирующего")
    contact: str | None = Field(default=None, description="Телеграм, телефон или email")
    note: str | None = Field(default=None, description="Комментарий к брони")


class WishItemPublic(BaseModel):
    id: int
    title: str
    description: str | None
    link: str | None
    price: str | None
    reserved: bool
    reserved_by: str | None
    reserved_contact: str | None
    reserved_note: str | None
    reserved_at: datetime | None
    image_url: str | None


class PostCreate(BaseModel):
    title: str
    summary: str
    body: str
    tags: List[str] = Field(default_factory=list)


class PostUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    body: str | None = None
    tags: List[str] | None = None


class PostPublic(BaseModel):
    id: int
    title: str
    summary: str
    body: str
    tags: List[str]
    created_at: datetime
