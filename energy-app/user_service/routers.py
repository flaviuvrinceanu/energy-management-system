from fastapi import APIRouter, HTTPException, Header
from typing import Literal, List, Optional
import httpx
import os
from .dto import UserIn, UserOut
from .schemas import User, Role

AUTH_SERVICE_URL = "http://auth:8001"

def require_admin(x_user_role: str | None = Header(default=None)):
    if x_user_role != "admin":
        raise HTTPException(403, "Forbidden")

def init_routes(app, SessionLocal):

    @app.get("/users")
    def get_users(x_user_role: Optional[str] = Header(None)) -> List[UserOut]:
        """Get all users from the users service database (admin only)"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")

        with SessionLocal() as db:
            rows = db.query(User).order_by(User.username.asc()).all()
            # Handle role stored as Enum or string
            def role_to_str(r):
                return r.value if hasattr(r, "value") else r

            return [
                UserOut(
                    id=str(u.id),
                    username=u.username,
                    role=role_to_str(u.role),
                )
                for u in rows
            ]

    @app.post("/users")
    def create_user(payload: UserIn, x_user_role: Optional[str] = Header(None)):
        """Create user via auth service"""
        if x_user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        print(f"Creating user: {payload.username}, role: {payload.role}")  # Debug
        
        try:
            response = httpx.post(
                f"{AUTH_SERVICE_URL}/auth/register",
                json={"username": payload.username, "password": payload.password, "role": payload.role},
                timeout=10.0
            )
            print(f"Auth response status: {response.status_code}")  # Debug
            print(f"Auth response body: {response.text}")  # Debug
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