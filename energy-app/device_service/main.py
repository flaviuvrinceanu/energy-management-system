import os
import threading
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from device_service.routers import init_routes
from device_service.schemas import Base
from device_service.consumer import DeviceSyncConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = (
    os.getenv("DEVICES_DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or "postgresql+psycopg://postgres:postgres@db:5432/energy_devices"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(engine)

app = FastAPI(title="Device Service", root_path="/devicesvc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_routes(app, SessionLocal)


consumer = DeviceSyncConsumer(SessionLocal)

@app.on_event("startup")
async def startup_event():
    """Start the RabbitMQ consumer in a background thread"""
    def run_consumer():
        try:
            logger.info("Starting device sync consumer thread...")
            consumer.start()
        except Exception as e:
            logger.error(f"Consumer thread failed: {e}", exc_info=True)
    
    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()
    logger.info("Device sync consumer thread launched")