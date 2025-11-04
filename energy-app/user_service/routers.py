from fastapi import APIRouter, HTTPException, Header
from typing import Literal, List
from .dto import *
from .schemas import *

def require_admin(x_user_role: str | None = Header(default=None)):
    if x_user_role != "admin":
        raise HTTPException(403, "Forbidden")

def init_routes(app, SessionLocal):
    @app.get("/users", response_model=List[UserOut])
    def list_users(_: None = require_admin):
        with SessionLocal() as db:
            return db.query(User).all()

    @app.post("/users", response_model=UserOut)
    def create_user(payload: UserIn, _: None = require_admin):
        with SessionLocal() as db:
            if db.query(User).filter(User.username == payload.username).first():
                raise HTTPException(400, "Username exists")
            u = User(username=payload.username, role=Role(payload.role))
            db.add(u); db.commit(); db.refresh(u)
            return u

    @app.get("/users/{uid}", response_model=UserOut)
    def get_user(uid: str, _: None = require_admin):
        with SessionLocal() as db:
            u = db.query(User).get(uid)
            if not u: raise HTTPException(404, "Not found")
            return u

    @app.put("/users/{uid}", response_model=UserOut)
    def update_user(uid: str, payload: UserIn, _: None = require_admin):
        with SessionLocal() as db:
            u = db.query(User).get(uid)
            if not u: raise HTTPException(404, "Not found")
            u.username = payload.username; u.role = Role(payload.role)
            db.commit(); db.refresh(u)
            return u

    @app.delete("/users/{uid}")
    def delete_user(uid: str, _: None = require_admin):
        with SessionLocal() as db:
            u = db.query(User).get(uid)
            if not u: raise HTTPException(404, "Not found")
            db.delete(u); db.commit()
            return {"ok": True}