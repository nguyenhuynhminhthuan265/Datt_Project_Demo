from typing import List, Optional

from pydantic import BaseModel


class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class UserPutToken(BaseModel):
    access_token: str


class User(UserBase):
    id: int
    is_active: bool
    access_token: str
    items: List[Item] = []

    class Config:
        orm_mode = True


class MessageEntityCreate(BaseModel):
    message: str
    id_user_sender: int
    id_user_receiver: int


class MessageEntity(BaseModel):
    id: int
    message: str
    id_user_sender: int
    id_user_receiver: int

    class Config:
        orm_mode = True
