import os, jwt, datetime as dt
from fastapi import FastAPI
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from auth_service.dto import *
from auth_service.routers import init_routes
from auth_service.schemas import Base

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "120"))
AUTH_DATABASE_URL = os.getenv("AUTH_DATABASE_URL", "postgresql+psycopg://postgres:flaviu@localhost:5432/energy_auth")

engine = create_engine(AUTH_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
Base.metadata.create_all(engine)

app = FastAPI(title="Auth Service", root_path="/auth")  # << add root_path

def make_token(sub: str, role: str) -> str:
    exp = dt.datetime.utcnow() + dt.timedelta(minutes=JWT_EXPIRES_MIN)
    return jwt.encode({"sub": sub, "role": role, "exp": exp}, JWT_SECRET, algorithm="HS256")

init_routes(app, SessionLocal, pwd, make_token)
