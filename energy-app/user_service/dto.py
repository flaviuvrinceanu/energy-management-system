from pydantic import BaseModel, Field
from typing import Literal

class UserIn(BaseModel):
    username: str
    role: Literal["admin","client"] = "client"

class UserOut(UserIn):
    id: str
