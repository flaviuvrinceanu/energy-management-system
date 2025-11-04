import os
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from device_service.schemas import Base
from device_service.routers import init_routes

load_dotenv()

DEVICES_DATABASE_URL = os.getenv("DEVICES_DATABASE_URL", "postgresql+psycopg://postgres:flaviu@localhost:5432/energy_devices")

engine = create_engine(DEVICES_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base.metadata.create_all(engine)

app = FastAPI(title="Device Service", root_path="/devicesvc")  
init_routes(app, SessionLocal)