from pydantic import BaseModel, Field
from typing import Literal

class UserIn(BaseModel):
    username: str
    password: str
    role: Literal["admin","client"] = "client"

class UserOut(BaseModel):
    id: str
    username: str
    role: str
