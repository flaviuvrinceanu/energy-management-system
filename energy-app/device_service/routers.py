from fastapi import HTTPException, Header
from typing import List
from .dto import DeviceIn, DeviceOut, DeviceUserIn
from .schemas import Device, DeviceUser

def require_admin(x_user_role: str | None = Header(default=None)):
    if x_user_role != "admin":
        raise HTTPException(403, "Forbidden")

def init_routes(app, SessionLocal):

    @app.post("/device-users")
    def upsert_device_user(payload: DeviceUserIn, x_user_role: str | None = Header(default=None)):
        require_admin(x_user_role)
        with SessionLocal() as db:
            u = db.get(DeviceUser, payload.id)
            if u:
                u.username = payload.username
                u.role = payload.role
            else:
                u = DeviceUser(id=payload.id, username=payload.username, role=payload.role)
                db.add(u)
            db.commit()
            return {"id": u.id, "username": u.username, "role": u.role}

    @app.get("/device-users/{uid}")
    def get_device_user(uid: str, x_user_role: str | None = Header(default=None)):
        require_admin(x_user_role)
        with SessionLocal() as db:
            u = db.get(DeviceUser, uid)
            if not u:
                raise HTTPException(404, "Not found")
            return {"id": u.id, "username": u.username, "role": u.role}

    @app.delete("/device-users/{uid}")
    def delete_device_user(uid: str, x_user_role: str | None = Header(default=None)):
        require_admin(x_user_role)
        with SessionLocal() as db:
            u = db.get(DeviceUser, uid)
            if u:
                db.delete(u); db.commit()
            return {"ok": True}

    @app.get("/devices", response_model=List[DeviceOut])
    def list_devices(x_user_role: str | None = Header(default=None)):
        require_admin(x_user_role)
        with SessionLocal() as db:
            ds = db.query(Device).all()
            return [{"id": d.id, "name": d.name, "max_consumption": d.max_consumption, "device_user_id": d.owner_user_id} for d in ds]

    @app.post("/devices", response_model=DeviceOut)
    def create_device(payload: DeviceIn, x_user_role: str | None = Header(default=None)):
        require_admin(x_user_role)
        with SessionLocal() as db:
            if payload.device_user_id and not db.get(DeviceUser, payload.device_user_id):
                raise HTTPException(400, "device_user_id not found")
            d = Device(name=payload.name, max_consumption=payload.max_consumption, owner_user_id=payload.device_user_id)
            db.add(d); db.commit(); db.refresh(d)
            return {"id": d.id, "name": d.name, "max_consumption": d.max_consumption, "device_user_id": d.owner_user_id}

    @app.get("/devices/{did}", response_model=DeviceOut)
    def get_device(did: str, x_user_role: str | None = Header(default=None)):
        require_admin(x_user_role)
        with SessionLocal() as db:
            d = db.get(Device, did)
            if not d:
                raise HTTPException(404, "Not found")
            return {"id": d.id, "name": d.name, "max_consumption": d.max_consumption, "device_user_id": d.owner_user_id}

    @app.put("/devices/{did}", response_model=DeviceOut)
    def update_device(did: str, payload: DeviceIn, x_user_role: str | None = Header(default=None)):
        require_admin(x_user_role)
        with SessionLocal() as db:
            d = db.get(Device, did)
            if not d:
                raise HTTPException(404, "Not found")
            if payload.device_user_id and not db.get(DeviceUser, payload.device_user_id):
                raise HTTPException(400, "device_user_id not found")
            d.name = payload.name
            d.max_consumption = payload.max_consumption
            d.owner_user_id = payload.device_user_id
            db.commit(); db.refresh(d)
            return {"id": d.id, "name": d.name, "max_consumption": d.max_consumption, "device_user_id": d.owner_user_id}

    @app.delete("/devices/{did}")
    def delete_device(did: str, x_user_role: str | None = Header(default=None)):
        require_admin(x_user_role)
        with SessionLocal() as db:
            d = db.get(Device, did)
            if d:
                db.delete(d); db.commit()
            return {"ok": True}

    @app.post("/devices/{did}/assign/{uid}")
    def assign(did: str, uid: str, x_user_role: str | None = Header(default=None)):
        require_admin(x_user_role)
        with SessionLocal() as db:
            d = db.get(Device, did)
            if not d:
                raise HTTPException(404, "Device not found")
            if not db.get(DeviceUser, uid):
                db.add(DeviceUser(id=uid, username="unknown", role="client"))
                db.flush()
            d.owner_user_id = uid
            db.commit()
            return {"id": d.id, "owner_user_id": d.owner_user_id}

    @app.delete("/devices/{did}/assign/{uid}")
    def unassign(did: str, uid: str, x_user_role: str | None = Header(default=None)):
        require_admin(x_user_role)
        with SessionLocal() as db:
            d = db.get(Device, did)
            if d and d.owner_user_id == uid:
                d.owner_user_id = None
                db.commit()
            return {"ok": True}

    @app.get("/devices/mine", response_model=List[DeviceOut])
    def mine(x_user_id: str | None = Header(default=None)):
        if not x_user_id:
            raise HTTPException(401, "Missing identity")
        with SessionLocal() as db:
            ds = db.query(Device).filter(Device.owner_user_id == x_user_id).all()
            return [{"id": d.id, "name": d.name, "max_consumption": d.max_consumption, "device_user_id": d.owner_user_id} for d in ds]
