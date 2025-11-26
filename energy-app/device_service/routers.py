from fastapi import HTTPException, Header
from typing import List, Optional
from .dto import DeviceIn, DeviceOut, DeviceUserIn, DeviceUpdateIn
from .schemas import Device, DeviceUser
import sys
import logging
sys.path.append('/app')
from shared.rabbitmq_utils import RabbitMQClient

logger = logging.getLogger(__name__)


rabbitmq_client = RabbitMQClient()

def init_routes(app, SessionLocal):

    @app.on_event("startup")
    async def startup_event():
        """Initialize RabbitMQ connection and declare exchanges"""
        try:
            rabbitmq_client.connect()
            rabbitmq_client.declare_exchange("sync_events", "fanout")
            logger.info("Device service connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Close RabbitMQ connection"""
        rabbitmq_client.close()

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
            
          
            try:
                event = {
                    "event_type": "DEVICE_CREATED",
                    "device_id": str(d.id),
                    "name": d.name,
                    "max_consumption": d.max_consumption,
                    "device_user_id": str(d.device_user_id) if d.device_user_id else None
                }
                rabbitmq_client.publish(None, event, exchange="sync_events")
                logger.info(f"Published DEVICE_CREATED event for device {d.id}")
            except Exception as e:
                logger.error(f"Failed to publish DEVICE_CREATED event: {e}")
            
            return DeviceOut(
                id=str(d.id),
                name=d.name,
                max_consumption=d.max_consumption,
                device_user_id=str(d.device_user_id) if d.device_user_id else None
            )

    @app.put("/devices/{device_id}")
    def update_device(device_id: str, payload: DeviceUpdateIn, x_user_role: Optional[str] = Header(None)) -> DeviceOut:
        """Update a device (admin only)"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        with SessionLocal() as db:
            d = db.query(Device).filter(Device.id == device_id).first()
            if not d:
                raise HTTPException(status_code=404, detail="Device not found")
            if payload.name is not None:
                d.name = payload.name
            if payload.max_consumption is not None:
                d.max_consumption = payload.max_consumption
            db.commit()
            db.refresh(d)
            
           
            try:
                event = {
                    "event_type": "DEVICE_UPDATED",
                    "device_id": str(d.id),
                    "name": d.name,
                    "max_consumption": d.max_consumption,
                    "device_user_id": str(d.device_user_id) if d.device_user_id else None
                }
                rabbitmq_client.publish(None, event, exchange="sync_events")
                logger.info(f"Published DEVICE_UPDATED event for device {d.id}")
            except Exception as e:
                logger.error(f"Failed to publish DEVICE_UPDATED event: {e}")
            
            return {
                "id": str(d.id),
                "name": d.name,
                "max_consumption": d.max_consumption,
                "device_user_id": str(d.device_user_id) if d.device_user_id else None,
            }

    @app.delete("/devices/{device_id}")
    def delete_device(device_id: str, x_user_role: Optional[str] = Header(None)):
        """Delete a device (admin only)"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        with SessionLocal() as db:
            d = db.query(Device).filter(Device.id == device_id).first()
            if not d:
                raise HTTPException(status_code=404, detail="Device not found")
            
            device_id_str = str(d.id)
            db.delete(d)
            db.commit()
            
           
            try:
                event = {
                    "event_type": "DEVICE_DELETED",
                    "device_id": device_id_str
                }
                rabbitmq_client.publish(None, event, exchange="sync_events")
                logger.info(f"Published DEVICE_DELETED event for device {device_id_str}")
            except Exception as e:
                logger.error(f"Failed to publish DEVICE_DELETED event: {e}")
            
            return {"message": "Device deleted"}

    @app.post("/devices/{device_id}/assign/{user_id}")
    def assign_device(device_id: str, user_id: str, x_user_role: Optional[str] = Header(None)):
        """Assign device to user (admin only)"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        with SessionLocal() as db:
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                raise HTTPException(status_code=404, detail="Device not found")
            
            user = db.query(DeviceUser).filter(DeviceUser.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            old_user_id = str(device.device_user_id) if device.device_user_id else None
            device.device_user_id = user_id
            db.commit()
            
           
            try:
                event = {
                    "event_type": "DEVICE_ASSIGNED",
                    "device_id": device_id,
                    "user_id": user_id,
                    "old_user_id": old_user_id
                }
                rabbitmq_client.publish(None, event, exchange="sync_events")
                logger.info(f"Published DEVICE_ASSIGNED event: device {device_id} → user {user_id}")
            except Exception as e:
                logger.error(f"Failed to publish DEVICE_ASSIGNED event: {e}")
            
            return {"message": f"Device {device_id} assigned to user {user_id}"}

    @app.post("/devices/{device_id}/unassign")
    def unassign_device(device_id: str, x_user_role: Optional[str] = Header(None)):
        """Unassign device from user (admin only)"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        with SessionLocal() as db:
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                raise HTTPException(status_code=404, detail="Device not found")
            
            old_user_id = str(device.device_user_id) if device.device_user_id else None
            device.device_user_id = None
            db.commit()
            
            
            try:
                event = {
                    "event_type": "DEVICE_UNASSIGNED",
                    "device_id": device_id,
                    "old_user_id": old_user_id
                }
                rabbitmq_client.publish(None, event, exchange="sync_events")
                logger.info(f"Published DEVICE_UNASSIGNED event: device {device_id}")
            except Exception as e:
                logger.error(f"Failed to publish DEVICE_UNASSIGNED event: {e}")
            
            return {"message": f"Device {device_id} unassigned"}

    @app.get("/device-users")
    def get_device_users(x_user_role: Optional[str] = Header(None)):
        """Get all device users (admin only)"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        with SessionLocal() as db:
            users = db.query(DeviceUser).all()
            return [{"id": str(u.id), "username": u.username, "role": u.role} for u in users]


