import os
import threading
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from monitoring_service.routers import init_routes
from monitoring_service.schemas import Base
from monitoring_service.consumer import MonitoringConsumer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("MONITORING_DATABASE_URL", "postgresql+psycopg://postgres:postgres@db:5432/energy_monitoring")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

try:
    Base.metadata.create_all(engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create tables: {e}")

app = FastAPI(title="Monitoring Service", root_path="/monitoring")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_routes(app, SessionLocal)

consumer = MonitoringConsumer(SessionLocal)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting monitoring consumers...")
    try:
        sync_thread = threading.Thread(target=consumer.start_sync_consumer, daemon=True)
        sync_thread.start()
        logger.info("Sync consumer thread started")
        
        data_thread = threading.Thread(target=consumer.start_data_consumer, daemon=True)
        data_thread.start()
        logger.info("Data consumer thread started")
    except Exception as e:
        logger.error(f"Failed to start consumers: {e}")