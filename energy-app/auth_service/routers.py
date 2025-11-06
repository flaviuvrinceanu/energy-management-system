import os
import time
import httpx
from fastapi import HTTPException
from .dto import RegisterIn, LoginIn, TokenOut
from .schemas import User, Role

USERS_SERVICE_URL = os.getenv("USERS_URL", "http://users:8002")
DEVICES_SERVICE_URL = os.getenv("DEVICES_URL", "http://devices:8003")

def init_routes(app, SessionLocal, pwd, make_token):

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
            
            # Sync to users service
            try:
                httpx.post(f"{USERS_SERVICE_URL}/users/sync", 
                          json={"id": str(u.id), "username": u.username, "role": u.role.value},
                          timeout=5.0)
            except Exception as e:
                print(f"Failed to sync to users service: {e}")
            
            # Sync to devices service 
            try:
                httpx.post(f"{DEVICES_SERVICE_URL}/device-users", 
                          json={"id": str(u.id), "username": u.username, "role": u.role.value},
                          headers={"X-User-Role": "admin"},
                          timeout=5.0)
            except Exception as e:
                print(f"Failed to sync to devices service: {e}")
            
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
        """Delete user from auth DB and cleanup to users and devices services."""
        with SessionLocal() as db:
            u = db.query(User).filter(User.id == user_id).first()
            if not u:
                raise HTTPException(status_code=404, detail="User not found")
            db.delete(u)
            db.commit()

        def call_with_retries(method: str, url: str, **kwargs):
            for i in range(3):
                try:
                    r = httpx.request(method, url, timeout=5.0, **kwargs)
                    
                    if r.status_code < 500:
                        return r
                except Exception:
                    pass
                time.sleep(0.5 * (2 ** i))
            return None

        # best effort
        call_with_retries("DELETE", f"{USERS_SERVICE_URL}/users/sync/{user_id}")
        call_with_retries("DELETE", f"{DEVICES_SERVICE_URL}/device-users/{user_id}")

        return {"status": "deleted", "id": user_id}
