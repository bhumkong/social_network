from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str
    last_visit: Optional[datetime]
    last_login: Optional[datetime]


class UserAuth(User):
    password_hash: str


class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class Post(BaseModel):
    id: int
    title: str
    body: str
    author: User
    like_count: int = 0


class PostCreate(BaseModel):
    title: str
    body: str


class Like(BaseModel):
    user_id: int
    post_id: int
    datetime: datetime


class RowCreationResult(Enum):
    CREATED = 1
    UNIQUE_VIOLATION = 2
    FOREIGN_KEY_VIOLATION = 3
