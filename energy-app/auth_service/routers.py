import os
import time
import httpx
from fastapi import HTTPException
from .dto import RegisterIn, LoginIn, TokenOut
from .schemas import User, Role
from pydantic import BaseModel
import sys
sys.path.append('/app')
from shared.rabbitmq_utils import RabbitMQClient

USERS_SERVICE_URL = os.getenv("USERS_URL", "http://users:8002")
DEVICES_SERVICE_URL = os.getenv("DEVICES_URL", "http://devices:8003")

class UpdateUserIn(BaseModel):
    username: str


rabbitmq_client = RabbitMQClient()

def init_routes(app, SessionLocal, pwd, make_token):

    @app.on_event("startup")
    async def startup_event():
        """Initialize RabbitMQ connection and declare exchanges"""
        try:
            rabbitmq_client.connect()
            rabbitmq_client.declare_exchange("sync_events", "fanout")
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {e}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Close RabbitMQ connection"""
        rabbitmq_client.close()

    @app.post("/auth/register")
    def register(payload: RegisterIn):
        with SessionLocal() as db:
            if db.query(User).filter(User.username == payload.username).first():
                raise HTTPException(status_code=400, detail="Username already exists")
            
            password_bytes = payload.password.encode('utf-8')[:72]
            password_str = password_bytes.decode('utf-8', errors='ignore')
            
            u = User(
                username=payload.username,
                password_hash=pwd.hash(password_str),
                role=Role(payload.role)
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            
           
            try:
                event = {
                    "event_type": "USER_CREATED",
                    "user_id": str(u.id),
                    "username": u.username,
                    "role": u.role.value
                }
                rabbitmq_client.publish(None, event, exchange="sync_events")
                print(f"Published USER_CREATED event for user {u.id}")
            except Exception as e:
                print(f"Failed to publish USER_CREATED event: {e}")
            
            return {"id": str(u.id), "username": u.username, "role": u.role.value}

    @app.post("/auth/login", response_model=TokenOut)
    def login(payload: LoginIn):
        with SessionLocal() as db:
            u = db.query(User).filter(User.username == payload.username).first()
            if not u or not pwd.verify(payload.password, u.password_hash):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            token = make_token(str(u.id), u.username, u.role.value)
            return TokenOut(access_token=token, token_type="bearer")

    @app.get("/auth/users")  
    def get_all_users():
        """Get all users for admin dashboard"""
        with SessionLocal() as db:
            users = db.query(User).all()
            return [{"id": str(u.id), "username": u.username, "role": u.role.value} for u in users]

    @app.delete("/auth/users/{user_id}")
    def delete_user(user_id: str):
        """Delete user from auth DB and publish USER_DELETED event."""
        with SessionLocal() as db:
            u = db.query(User).filter(User.id == user_id).first()
            if not u:
                raise HTTPException(status_code=404, detail="User not found")
            
            user_data = {"id": str(u.id), "username": u.username, "role": u.role.value}
            db.delete(u)
            db.commit()

       
        try:
            event = {
                "event_type": "USER_DELETED",
                "user_id": user_id
            }
            rabbitmq_client.publish(None, event, exchange="sync_events")
            print(f"Published USER_DELETED event for user {user_id}")
        except Exception as e:
            print(f"Failed to publish USER_DELETED event: {e}")

        return {"status": "deleted", "id": user_id}

    @app.put("/auth/users/{user_id}")
    def update_user(user_id: str, payload: UpdateUserIn):
        """Update username in Auth and publish USER_UPDATED event."""
        with SessionLocal() as db:
            u = db.query(User).filter(User.id == user_id).first()
            if not u:
                raise HTTPException(status_code=404, detail="User not found")
            
            exists = db.query(User).filter(User.username == payload.username, User.id != user_id).first()
            if exists:
                raise HTTPException(status_code=409, detail="Username already exists")
            
            u.username = payload.username
            db.commit()
            db.refresh(u)

        
        try:
            event = {
                "event_type": "USER_UPDATED",
                "user_id": str(u.id),
                "username": u.username,
                "role": u.role.value if hasattr(u.role, "value") else u.role
            }
            rabbitmq_client.publish(None, event, exchange="sync_events")
            print(f"Published USER_UPDATED event for user {u.id}")
        except Exception as e:
            print(f"Failed to publish USER_UPDATED event: {e}")

        return {"id": str(u.id), "username": u.username, "role": u.role.value if hasattr(u.role, "value") else u.role}
