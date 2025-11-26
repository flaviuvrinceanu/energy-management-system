import sys
sys.path.append('/app')
from shared.rabbitmq_utils import RabbitMQClient
from .schemas import MonitoringDevice, HourlyMeasurement
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MonitoringConsumer:
    def __init__(self, SessionLocal):
        self.SessionLocal = SessionLocal
        self.rabbitmq_sync = RabbitMQClient()
        self.rabbitmq_data = RabbitMQClient()
    
    def handle_sync_message(self, message: dict):
        """Handle device lifecycle events"""
        event_type = message.get("event_type")
        
        if event_type == "DEVICE_CREATED":
            self._handle_device_created(message)
        elif event_type == "DEVICE_UPDATED":
            self._handle_device_updated(message)
        elif event_type == "DEVICE_DELETED":
            self._handle_device_deleted(message)
        elif event_type == "DEVICE_ASSIGNED":
            self._handle_device_assigned(message)
        elif event_type == "DEVICE_UNASSIGNED":
            self._handle_device_unassigned(message)
        else:
            logger.warning(f"Unknown event type in sync_queue: {event_type}")
    
    def _handle_device_created(self, message: dict):
        """Handle DEVICE_CREATED event"""
        with self.SessionLocal() as db:
            existing = db.query(MonitoringDevice).filter(
                MonitoringDevice.device_id == message["device_id"]
            ).first()
            
            if not existing:
                device = MonitoringDevice(
                    device_id=message["device_id"],
                    name=message["name"],
                    max_consumption=message["max_consumption"],
                    user_id=message.get("device_user_id")  
                )
                db.add(device)
                db.commit()
                logger.info(f"Created monitoring device {message['device_id']}")
    
    def _handle_device_updated(self, message: dict):
        """Handle DEVICE_UPDATED event"""
        with self.SessionLocal() as db:
            device = db.query(MonitoringDevice).filter(
                MonitoringDevice.device_id == message["device_id"]
            ).first()
            
            if device:
                device.name = message["name"]
                device.max_consumption = message["max_consumption"]
                device.user_id = message.get("device_user_id")  
                db.commit()
                logger.info(f"Updated monitoring device {message['device_id']}")
    
    def _handle_device_deleted(self, message: dict):
        """Handle DEVICE_DELETED event"""
        with self.SessionLocal() as db:
            device = db.query(MonitoringDevice).filter(
                MonitoringDevice.device_id == message["device_id"]
            ).first()
            
            if device:
                
                db.query(HourlyMeasurement).filter(
                    HourlyMeasurement.device_id == message["device_id"]
                ).delete()
                
               
                db.delete(device)
                db.commit()
                logger.info(f"Deleted monitoring device {message['device_id']} and its measurements")
            else:
                logger.warning(f"Device {message['device_id']} not found for deletion")
    
    def _handle_device_assigned(self, message: dict):
        """Handle DEVICE_ASSIGNED event"""
        with self.SessionLocal() as db:
            device = db.query(MonitoringDevice).filter(
                MonitoringDevice.device_id == message["device_id"]
            ).first()
            
            if device:
                device.user_id = message["user_id"]
                db.commit()
                logger.info(f"Assigned device {message['device_id']} to user {message['user_id']}")
            else:
                logger.warning(f"Device {message['device_id']} not found for assignment")
    
    def _handle_device_unassigned(self, message: dict):
        """Handle DEVICE_UNASSIGNED event"""
        with self.SessionLocal() as db:
            device = db.query(MonitoringDevice).filter(
                MonitoringDevice.device_id == message["device_id"]
            ).first()
            
            if device:
                device.user_id = None
                db.commit()
                logger.info(f"Unassigned device {message['device_id']} from user {message.get('old_user_id')}")
            else:
                logger.warning(f"Device {message['device_id']} not found for unassignment")
    
    def handle_device_data(self, message: dict):
        """Handle device measurement data"""
        try:
            
            timestamp = datetime.fromisoformat(message["timestamp"].replace('Z', '+00:00'))
            device_id = message["device_id"]
            measurement_value = float(message["measurement_value"])
            
           
            hour_timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
            
            with self.SessionLocal() as db:
                
                device = db.query(MonitoringDevice).filter(
                    MonitoringDevice.device_id == device_id
                ).first()
                
                if not device:
                    logger.warning(f"Device {device_id} not found in monitoring DB")
                    return
                
                
                measurement = db.query(HourlyMeasurement).filter(
                    HourlyMeasurement.device_id == device_id,
                    HourlyMeasurement.hour_timestamp == hour_timestamp
                ).first()
                
                if measurement:
                    measurement.total_kwh += measurement_value
                else:
                    measurement = HourlyMeasurement(
                        device_id=device_id,
                        hour_timestamp=hour_timestamp,
                        total_kwh=measurement_value
                    )
                    db.add(measurement)
                
                db.commit()
                logger.info(f"Updated measurement for device {device_id} at {hour_timestamp}: {measurement.total_kwh} kWh")
        
        except Exception as e:
            logger.error(f"Error processing device data: {e}")
    
    def start_sync_consumer(self):
        """Start consuming sync events"""
        self.rabbitmq_sync.connect()
        self.rabbitmq_sync.declare_exchange("sync_events", "fanout")
        self.rabbitmq_sync.declare_queue("monitoring_service_sync_queue")
        self.rabbitmq_sync.bind_queue_to_exchange("monitoring_service_sync_queue", "sync_events")
        logger.info("Monitoring sync consumer started")
        self.rabbitmq_sync.consume("monitoring_service_sync_queue", self.handle_sync_message)
    
    def start_data_consumer(self):
        """Start consuming device data"""
        self.rabbitmq_data.connect()
        self.rabbitmq_data.declare_queue("device_data_queue")
        logger.info("Monitoring data consumer started")
        self.rabbitmq_data.consume("device_data_queue", self.handle_device_data)