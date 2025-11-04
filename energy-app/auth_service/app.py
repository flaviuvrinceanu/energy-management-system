from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
import os, jwt, datetime as dt, enum, uuid
from passlib.context import CryptContext
from sqlalchemy import create_engine, String, Enum
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from dotenv import load_dotenv
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "120"))
DATABASE_URL = os.getenv("AUTH_DATABASE_URL", "postgresql+psycopg://postgres:flaviu@localhost:5432/energy_auth")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Base(DeclarativeBase): pass

class Role(str, enum.Enum):
    admin = "admin"
    client = "client"



class User(Base):
    __tablename__ = "auth_users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.client)

Base.metadata.create_all(engine)

class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6)
    role: Literal["admin","client"] = "client"

class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

app = FastAPI(title="Auth Service")

def make_token(sub: str, role: str) -> str:
    exp = dt.datetime.utcnow() + dt.timedelta(minutes=JWT_EXPIRES_MIN)
    return jwt.encode({"sub": sub, "role": role, "exp": exp}, JWT_SECRET, algorithm="HS256")

@app.post("/auth/register")
def register(payload: RegisterIn):
    with SessionLocal() as db:
        if db.query(User).filter(User.username == payload.username).first():
            raise HTTPException(400, "Username exists")
        u = User(username=payload.username, password_hash=pwd.hash(payload.password), role=Role(payload.role))
        db.add(u); db.commit(); db.refresh(u)
        return {"id": u.id, "username": u.username, "role": u.role.value}

@app.post("/auth/login", response_model=TokenOut)
def login(payload: LoginIn):
    with SessionLocal() as db:
        u = db.query(User).filter(User.username == payload.username).first()
        if not u or not pwd.verify(payload.password, u.password_hash):
            raise HTTPException(401, "Invalid credentials")
        return TokenOut(access_token=make_token(u.id, u.role.value))
