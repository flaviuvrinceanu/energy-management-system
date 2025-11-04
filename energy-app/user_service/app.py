from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Literal, List
import os, enum, uuid
from sqlalchemy import create_engine, String, Enum
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("USERS_DATABASE_URL", "postgresql+psycopg://postgres:flaviu@localhost:5432/energy_users")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase): pass

class Role(str, enum.Enum):
    admin = "admin"
    client = "client"

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.client)

Base.metadata.create_all(engine)

class UserIn(BaseModel):
    username: str
    role: Literal["admin","client"] = "client"

class UserOut(UserIn):
    id: str

app = FastAPI(title="User Service")

def require_admin(x_user_role: str | None = Header(default=None)):
    if x_user_role != "admin":
        raise HTTPException(403, "Forbidden")

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
