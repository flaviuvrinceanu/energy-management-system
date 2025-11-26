from pydantic import BaseModel
from datetime import datetime
from typing import List

class DeviceDataIn(BaseModel):
    timestamp: str  
    device_id: str
    measurement_value: float  

class HourlyDataOut(BaseModel):
    hour: int  
    total_kwh: float

class DailyChartOut(BaseModel):
    device_id: str
    date: str
    hourly_data: List[HourlyDataOut]