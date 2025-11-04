from typing import Optional
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import uuid

class Base(DeclarativeBase):
    pass

class DeviceUser(Base):
    __tablename__ = "device_users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(16))

class Device(Base):
    __tablename__ = "devices"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120))
    max_consumption: Mapped[float] = mapped_column(Float)
    owner_user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("device_users.id"), index=True, nullable=True)

    # FIX: relationship must be annotated with Mapped[…]
    owner: Mapped["DeviceUser"] = relationship("DeviceUser", lazy="joined")