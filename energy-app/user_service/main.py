import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from user_service.routers import init_routes
from user_service.schemas import Base

load_dotenv()

DATABASE_URL = (
    os.getenv("USERS_DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or "postgresql+psycopg://postgres:postgres@db:5432/energy_users"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(engine)

app = FastAPI(title="User Service", root_path="/usersvc")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_routes(app, SessionLocal)