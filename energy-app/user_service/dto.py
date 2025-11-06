from pydantic import BaseModel, Field
from typing import Literal

class UserIn(BaseModel):
    username: str
    password: str
    role: str

class UserUpdateIn(BaseModel):
    username: str

class UserOut(BaseModel):
    id: str
    username: str
    role: str
