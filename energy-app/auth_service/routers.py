import os, httpx, jwt, datetime as dt
from fastapi import HTTPException
from .dto import RegisterIn, LoginIn, TokenOut
from .schemas import User, Role

USERS_URL = os.getenv("USERS_URL", "http://127.0.0.1:8002")
DEVICES_URL = os.getenv("DEVICES_URL", "http://127.0.0.1:8003")

def init_routes(app, SessionLocal, pwd, make_token):

    @app.post("/auth/register")
    def register(payload: RegisterIn):
        with SessionLocal() as db:
            if db.query(User).filter(User.username == payload.username).first():
                raise HTTPException(400, "Username exists")

            u = User(username=payload.username, password_hash=pwd.hash(payload.password), role=Role(payload.role))
            db.add(u); db.commit(); db.refresh(u)

            created_user_svc = False
            created_device_user = False
            created_device_id = None

            try:
                with httpx.Client(timeout=10.0) as client:
                   
                    resp = client.post(
                        f"{USERS_URL}/users",
                        headers={"x_user_role": "admin"},
                        json={"id": u.id, "username": u.username, "role": u.role.value},
                    )
                    if resp.status_code not in (200, 201):
                        raise HTTPException(resp.status_code, f"User service create failed: {resp.text}")
                    created_user_svc = True

                  
                    resp = client.post(
                        f"{DEVICES_URL}/device-users",
                        headers={"x_user_role": "admin"},
                        json={"id": u.id, "username": u.username, "role": u.role.value},
                    )
                    if resp.status_code not in (200, 201):
                        raise HTTPException(resp.status_code, f"Device-user upsert failed: {resp.text}")
                    created_device_user = True

                   
                    resp = client.post(
                        f"{DEVICES_URL}/devices",
                        headers={"x_user_role": "admin"},
                        json={"name": f"{u.username}-device", "max_consumption": 0.0, "device_user_id": u.id},
                    )
                    if resp.status_code not in (200, 201):
                        raise HTTPException(resp.status_code, f"Device create failed: {resp.text}")
                    created_device_id = resp.json().get("id")

                return {"id": u.id, "username": u.username, "role": u.role.value}

            except HTTPException as e:
                
                try:
                    if created_device_id:
                        with httpx.Client(timeout=5.0) as c:
                            c.delete(f"{DEVICES_URL}/devices/{created_device_id}", headers={"x_user_role": "admin"})
                except Exception: pass
                try:
                    if created_device_user:
                        with httpx.Client(timeout=5.0) as c:
                            c.delete(f"{DEVICES_URL}/device-users/{u.id}", headers={"x_user_role": "admin"})
                except Exception: pass
                try:
                    if created_user_svc:
                        with httpx.Client(timeout=5.0) as c:
                            c.delete(f"{USERS_URL}/users/{u.id}", headers={"x_user_role": "admin"})
                except Exception: pass
                try:
                    db.delete(u); db.commit()
                except Exception: pass
                raise e
            except Exception:
                try:
                    if created_device_id:
                        with httpx.Client(timeout=5.0) as c:
                            c.delete(f"{DEVICES_URL}/devices/{created_device_id}", headers={"x_user_role": "admin"})
                except Exception: pass
                try:
                    if created_device_user:
                        with httpx.Client(timeout=5.0) as c:
                            c.delete(f"{DEVICES_URL}/device-users/{u.id}", headers={"x_user_role": "admin"})
                except Exception: pass
                try:
                    if created_user_svc:
                        with httpx.Client(timeout=5.0) as c:
                            c.delete(f"{USERS_URL}/users/{u.id}", headers={"x_user_role": "admin"})
                except Exception: pass
                try:
                    db.delete(u); db.commit()
                except Exception: pass
                raise HTTPException(502, "Registration failed due to upstream error")

    @app.post("/auth/login", response_model=TokenOut)
    def login(payload: LoginIn):
        with SessionLocal() as db:
            u = db.query(User).filter(User.username == payload.username).first()
            if not u or not pwd.verify(payload.password, u.password_hash):
                raise HTTPException(401, "Invalid credentials")
            return TokenOut(access_token=make_token(u.id, u.role.value))
