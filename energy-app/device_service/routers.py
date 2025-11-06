from fastapi import HTTPException, Header
from typing import List, Optional
from .dto import DeviceIn, DeviceOut, DeviceUserIn
from .schemas import Device, DeviceUser

def init_routes(app, SessionLocal):

    @app.get("/devices/mine")
    def get_my_devices(x_user_id: Optional[str] = Header(None), x_user_role: Optional[str] = Header(None)):
        """Get devices assigned to the current user (client only)"""
        if not x_user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        with SessionLocal() as db:
            devices = db.query(Device).filter(Device.device_user_id == x_user_id).all()
            return [DeviceOut(
                id=str(d.id),
                name=d.name,
                max_consumption=d.max_consumption,
                device_user_id=str(d.device_user_id) if d.device_user_id else None
            ) for d in devices]

    @app.get("/devices")
    def get_devices(x_user_role: Optional[str] = Header(None)):
        """Get all devices (admin only)"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        with SessionLocal() as db:
            devices = db.query(Device).all()
            return [DeviceOut(
                id=str(d.id),
                name=d.name,
                max_consumption=d.max_consumption,
                device_user_id=str(d.device_user_id) if d.device_user_id else None
            ) for d in devices]

    @app.post("/devices")
    def create_device(payload: DeviceIn, x_user_role: Optional[str] = Header(None)):
        """Create a device (admin only)"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        with SessionLocal() as db:
            d = Device(
                name=payload.name,
                max_consumption=payload.max_consumption,
                device_user_id=payload.device_user_id
            )
            db.add(d)
            db.commit()
            db.refresh(d)
            return DeviceOut(
                id=str(d.id),
                name=d.name,
                max_consumption=d.max_consumption,
                device_user_id=str(d.device_user_id) if d.device_user_id else None
            )

    @app.put("/devices/{device_id}")
    def update_device(device_id: str, payload: DeviceIn, x_user_role: Optional[str] = Header(None)):
        """Update a device (admin only)"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        with SessionLocal() as db:
            d = db.query(Device).filter(Device.id == device_id).first()
            if not d:
                raise HTTPException(status_code=404, detail="Device not found")
            d.name = payload.name
            d.max_consumption = payload.max_consumption
            d.device_user_id = payload.device_user_id
            db.commit()
            db.refresh(d)
            return DeviceOut(
                id=str(d.id),
                name=d.name,
                max_consumption=d.max_consumption,
                device_user_id=str(d.device_user_id) if d.device_user_id else None
            )

    @app.delete("/devices/{device_id}")
    def delete_device(device_id: str, x_user_role: Optional[str] = Header(None)):
        """Delete a device (admin only)"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        with SessionLocal() as db:
            d = db.query(Device).filter(Device.id == device_id).first()
            if not d:
                raise HTTPException(status_code=404, detail="Device not found")
            db.delete(d)
            db.commit()
            return {"message": "Device deleted"}

    @app.post("/devices/{device_id}/assign/{user_id}")
    def assign_device(device_id: str, user_id: str, x_user_role: Optional[str] = Header(None)):
        """Assign a device to a user (admin only)"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        with SessionLocal() as db:
            d = db.query(Device).filter(Device.id == device_id).first()
            if not d:
                raise HTTPException(status_code=404, detail="Device not found")
            d.device_user_id = user_id
            db.commit()
            db.refresh(d)
            return DeviceOut(
                id=str(d.id),
                name=d.name,
                max_consumption=d.max_consumption,
                device_user_id=str(d.device_user_id) if d.device_user_id else None
            )

    @app.delete("/devices/{device_id}/assign/{user_id}")
    def unassign_device(device_id: str, user_id: str, x_user_role: Optional[str] = Header(None)):
        """Unassign a device from a user (admin only)"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        with SessionLocal() as db:
            d = db.query(Device).filter(Device.id == device_id).first()
            if not d:
                raise HTTPException(status_code=404, detail="Device not found")
            d.device_user_id = None
            db.commit()
            db.refresh(d)
            return DeviceOut(
                id=str(d.id),
                name=d.name,
                max_consumption=d.max_consumption,
                device_user_id=None
            )

    
    @app.get("/device-users")
    def get_device_users(x_user_role: Optional[str] = Header(None)):
        """Get all device users (admin only)"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        with SessionLocal() as db:
            users = db.query(DeviceUser).all()
            return [{"id": str(u.id), "username": u.username, "role": u.role.value} for u in users]

    @app.post("/device-users")
    def create_device_user(payload: DeviceUserIn):
        """Sync user from auth service"""
        with SessionLocal() as db:
            existing = db.query(DeviceUser).filter(DeviceUser.id == payload.id).first()
            if existing:
                existing.username = payload.username
                existing.role = payload.role
                db.commit()
                db.refresh(existing)
                u = existing  
            else:
                u = DeviceUser(id=payload.id, username=payload.username, role=payload.role)
                db.add(u)
                db.commit()
                db.refresh(u)
        
        return {"id": str(u.id), "username": u.username, "role": u.role}

    @app.delete("/device-users/{user_id}")
    def delete_device_user(user_id: str):
        """Internal: unassign all devices from user and remove device_user (called by auth on delete)."""
        with SessionLocal() as db:
    
            db.query(Device).filter(Device.device_user_id == user_id).update({"device_user_id": None})
           
            db.query(DeviceUser).filter(DeviceUser.id == user_id).delete()
            db.commit()
        return {"status": "deleted"}
