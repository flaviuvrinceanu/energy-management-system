from fastapi import HTTPException, Header
from typing import Optional
from datetime import datetime, timedelta, timezone
from .dto import DailyChartOut, HourlyDataOut
from .schemas import HourlyMeasurement, MonitoringDevice

def init_routes(app, SessionLocal):
    
    @app.get("/devices/{device_id}/day/{date}", response_model=DailyChartOut)
    def get_daily_chart(device_id: str, date: str, x_user_id: Optional[str] = Header(None), x_user_role: Optional[str] = Header(None)):
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        with SessionLocal() as db:
            device = db.query(MonitoringDevice).filter(MonitoringDevice.device_id == device_id).first()
            if not device:
                raise HTTPException(status_code=404, detail="Device not found")
            
            
            if x_user_role == "client" and device.user_id != x_user_id:
                raise HTTPException(status_code=403, detail="You can only view your own devices")
            
            hourly_data = {h: 0.0 for h in range(24)}
            start_time = date_obj.replace(tzinfo=timezone.utc)
            end_time = start_time + timedelta(days=1)
            
            measurements = db.query(HourlyMeasurement).filter(
                HourlyMeasurement.device_id == device_id,
                HourlyMeasurement.hour_timestamp >= start_time,
                HourlyMeasurement.hour_timestamp < end_time
            ).all()
            
            for m in measurements:
                hourly_data[m.hour_timestamp.hour] = m.total_kwh
            
            hourly_list = [HourlyDataOut(hour=h, total_kwh=hourly_data[h]) for h in range(24)]
            return DailyChartOut(device_id=device_id, date=date, hourly_data=hourly_list)
    
    @app.get("/devices")
    def get_all_devices(x_user_role: Optional[str] = Header(None)):
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        with SessionLocal() as db:
            devices = db.query(MonitoringDevice).all()
            return [{"device_id": d.device_id, "name": d.name, "max_consumption": d.max_consumption} for d in devices]