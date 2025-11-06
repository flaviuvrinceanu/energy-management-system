from typing import Optional
from sqlalchemy import String, Float, ForeignKey, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Base(DeclarativeBase):
    pass

class DeviceUser(Base):
    __tablename__ = "device_users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(16))

    devices = relationship("Device", back_populates="device_user")

class Device(Base):
    __tablename__ = "devices"
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(64))
    max_consumption: Mapped[float] = mapped_column(Float)
    device_user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("device_users.id"), nullable=True)

    device_user = relationship("DeviceUser", back_populates="devices")