from pydantic import BaseModel
from typing import Optional, List

class DeviceUserIn(BaseModel):
    id: str
    username: str
    role: str

class DeviceUserOut(DeviceUserIn):
    id: str

class DeviceIn(BaseModel):
    name: str
    max_consumption: float
    device_user_id: Optional[str] = None

class DeviceOut(DeviceIn):
    id: str
