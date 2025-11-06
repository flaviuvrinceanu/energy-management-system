import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from auth_service.routers import init_routes
from auth_service.schemas import Base

load_dotenv()

DATABASE_URL = os.getenv("AUTH_DATABASE_URL") or os.getenv("DATABASE_URL") or "postgresql+psycopg://postgres:postgres@db:5432/energy_auth"
JWT_SECRET = os.getenv("JWT_SECRET", "secret-key")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "120"))

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def make_token(user_id: str, username: str, role: str):
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MIN)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

app = FastAPI(title="Auth Service")  

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_routes(app, SessionLocal, pwd_context, make_token)
