from pydantic import BaseModel, Field
from typing import Literal

class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6)
    role: Literal["admin","client"] = "client"

class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"