from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List
import os, uuid
from sqlalchemy import create_engine, String, Float, UniqueConstraint
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv(
    "DEVICES_DATABASE_URL",
    "postgresql+psycopg://postgres:flaviu@localhost:5432/energy_devices"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Device(Base):
    __tablename__ = "devices"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120))
    max_consumption: Mapped[float] = mapped_column(Float)

class UserDevice(Base):
    __tablename__ = "user_devices"
    user_id: Mapped[str] = mapped_column(String, primary_key=True)     
    device_id: Mapped[str] = mapped_column(String, primary_key=True)   
    __table_args__ = (UniqueConstraint("user_id", "device_id", name="uq_user_device"),)

Base.metadata.create_all(engine)

class DeviceIn(BaseModel):
    name: str
    max_consumption: float

class DeviceOut(DeviceIn):
    id: str

app = FastAPI(title="Device Service")

def require_admin(x_user_role: str | None = Header(default=None)):
    if x_user_role != "admin":
        raise HTTPException(403, "Forbidden")



@app.get("/devices", response_model=List[DeviceOut], dependencies=[Depends(require_admin)])
def list_devices():
    with SessionLocal() as db:
        return db.query(Device).all()

@app.post("/devices", response_model=DeviceOut, dependencies=[Depends(require_admin)])
def create_device(payload: DeviceIn):
    with SessionLocal() as db:
        d = Device(name=payload.name, max_consumption=payload.max_consumption)
        db.add(d)
        db.commit()
        db.refresh(d)
        return d

@app.get("/devices/{did}", response_model=DeviceOut, dependencies=[Depends(require_admin)])
def get_device(did: str):
    with SessionLocal() as db:
        d = db.query(Device).get(did)
        if not d:
            raise HTTPException(404, "Not found")
        return d

@app.put("/devices/{did}", response_model=DeviceOut, dependencies=[Depends(require_admin)])
def update_device(did: str, payload: DeviceIn):
    with SessionLocal() as db:
        d = db.query(Device).get(did)
        if not d:
            raise HTTPException(404, "Not found")
        d.name = payload.name
        d.max_consumption = payload.max_consumption
        db.commit()
        db.refresh(d)
        return d

@app.delete("/devices/{did}", dependencies=[Depends(require_admin)])
def delete_device(did: str):
    with SessionLocal() as db:
        d = db.query(Device).get(did)
        if not d:
            raise HTTPException(404, "Not found")
        db.delete(d)
        db.commit()
        return {"ok": True}

@app.post("/devices/{did}/assign/{uid}", dependencies=[Depends(require_admin)])
def assign(did: str, uid: str):
    with SessionLocal() as db:
        db.merge(UserDevice(user_id=uid, device_id=did))
        db.commit()
        return {"ok": True}

@app.delete("/devices/{did}/assign/{uid}", dependencies=[Depends(require_admin)])
def unassign(did: str, uid: str):
    with SessionLocal() as db:
        link = db.query(UserDevice).filter_by(user_id=uid, device_id=did).first()
        if link:
            db.delete(link)
            db.commit()
        return {"ok": True}



@app.get("/devices/mine", response_model=List[DeviceOut])
def mine(x_user_id: str | None = Header(default=None)):
    if not x_user_id:
        raise HTTPException(401, "Missing identity")
    with SessionLocal() as db:
        dev_ids = [ud.device_id for ud in db.query(UserDevice).filter_by(user_id=x_user_id).all()]
        if not dev_ids:
            return []
        return db.query(Device).filter(Device.id.in_(dev_ids)).all()
