from sqlalchemy import String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional  

class Base(DeclarativeBase):
    pass

class MonitoringDevice(Base):
    __tablename__ = "monitoring_devices"
    device_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    max_consumption: Mapped[float] = mapped_column(Float)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  
    
    measurements = relationship("HourlyMeasurement", back_populates="device", cascade="all, delete-orphan")

class HourlyMeasurement(Base):
    __tablename__ = "hourly_measurements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String, ForeignKey("monitoring_devices.device_id"))
    hour_timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    total_kwh: Mapped[float] = mapped_column(Float, default=0.0)
    
    device = relationship("MonitoringDevice", back_populates="measurements")