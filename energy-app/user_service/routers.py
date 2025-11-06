from fastapi import APIRouter, HTTPException, Header
from typing import Optional, List
import httpx
import os
from .dto import *
from .schemas import User, Role

AUTH_SERVICE_URL = os.getenv("AUTH_URL", "http://auth:8001")

def require_admin(x_user_role: str | None = Header(default=None)):
    if x_user_role != "admin":
        raise HTTPException(403, "Forbidden")

def init_routes(app, SessionLocal):

    @app.get("/users")
    def get_users(x_user_role: Optional[str] = Header(None)):
        """Get all users from auth service"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        try:
            response = httpx.get(f"{AUTH_SERVICE_URL}/auth/users", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling auth service: {e}")
            raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")

    @app.post("/users")
    def create_user(payload: UserIn, x_user_role: Optional[str] = Header(None)):
        """Create user via auth service"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        print(f"Creating user: {payload.username}, role: {payload.role}") 
        
        try:
            response = httpx.post(
                f"{AUTH_SERVICE_URL}/auth/register",
                json={"username": payload.username, "password": payload.password, "role": payload.role},
                timeout=10.0
            )
            print(f"Auth response status: {response.status_code}")  
            print(f"Auth response body: {response.text}")  
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.headers.get('content-type') == 'application/json' else e.response.text
            print(f"HTTP error: {error_detail}")
            raise HTTPException(status_code=e.response.status_code, detail=error_detail)
        except Exception as e:
            print(f"Exception creating user: {type(e).__name__}: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Auth service error: {str(e)}")

    @app.post("/users/sync")
    def sync_user(payload: dict):
        """Internal sync endpoint"""
        with SessionLocal() as db:
            existing = db.query(User).filter(User.id == payload["id"]).first()
            if existing:
                existing.username = payload["username"]
                existing.role = Role(payload["role"])
            else:
                u = User(id=payload["id"], username=payload["username"], role=Role(payload["role"]))
                db.add(u)
            db.commit()
            return {"status": "synced"}

    @app.delete("/users/{user_id}")
    def delete_user(user_id: str, x_user_role: Optional[str] = Header(None)):
        """Delete user via auth service"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        try:
            response = httpx.delete(f"{AUTH_SERVICE_URL}/auth/users/{user_id}", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail"))
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

    @app.delete("/users/sync/{user_id}")
    def sync_delete_user(user_id: str):
        """Remove user from users DB (called by auth on delete)."""
        with SessionLocal() as db:
            db.query(User).filter(User.id == user_id).delete()
            db.commit()
        return {"status": "deleted"}

    @app.put("/users/{user_id}")
    def update_user(user_id: str, payload: UserUpdateIn, x_user_role: Optional[str] = Header(None)):
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")

        resp = httpx.put(f"{AUTH_SERVICE_URL}/auth/users/{user_id}", json={"username": payload.username}, timeout=10.0)
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail")
            except Exception:
                detail = resp.text
            raise HTTPException(status_code=resp.status_code, detail=detail)

        user_json = resp.json()
        with SessionLocal() as db:
            existing = db.query(User).filter(User.id == user_json["id"]).first()
            if existing:
                existing.username = user_json["username"]
                existing.role = Role(user_json["role"])
            else:
                db.add(User(id=user_json["id"], username=user_json["username"], role=Role(user_json["role"])))
            db.commit()
        return user_json