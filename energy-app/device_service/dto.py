from pydantic import BaseModel
from typing import Optional

class DeviceIn(BaseModel):
    name: str
    max_consumption: float
    device_user_id: Optional[str] = None

class DeviceUpdateIn(BaseModel):
    name: Optional[str] = None
    max_consumption: Optional[float] = None

class DeviceUserIn(BaseModel):
    id: str
    username: str
    role: str

class DeviceUserOut(DeviceUserIn):
    id: str

class DeviceOut(DeviceIn):
    id: str
