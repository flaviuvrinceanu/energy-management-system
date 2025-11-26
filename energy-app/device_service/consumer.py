import sys
sys.path.append('/app')
from shared.rabbitmq_utils import RabbitMQClient
from .schemas import DeviceUser
import logging

logger = logging.getLogger(__name__)

class DeviceSyncConsumer:
    def __init__(self, SessionLocal):
        self.SessionLocal = SessionLocal
        self.rabbitmq_client = RabbitMQClient()
    
    def handle_message(self, message: dict):
        """Handle incoming sync events"""
        event_type = message.get("event_type")
        if event_type == "USER_CREATED":
            self._handle_user_created(message)
        elif event_type == "USER_UPDATED":
            self._handle_user_updated(message)
        elif event_type == "USER_DELETED":
            self._handle_user_deleted(message)
        elif event_type == "DEVICE_CREATED":
           
            pass
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    def _handle_user_created(self, message: dict):
        """Handle USER_CREATED event"""
        logger.info(f"Processing USER_CREATED: {message}")
        with self.SessionLocal() as db:
            existing = db.query(DeviceUser).filter(DeviceUser.id == message["user_id"]).first()
            if not existing:
                user = DeviceUser(
                    id=message["user_id"],
                    username=message["username"],
                    role=message["role"]
                )
                db.add(user)
                db.commit()
                logger.info(f" Created device user {message['user_id']} ({message['username']})")
            else:
                logger.info(f" Device user {message['user_id']} already exists")
    
    def _handle_user_updated(self, message: dict):
        """Handle USER_UPDATED event"""
        with self.SessionLocal() as db:
            user = db.query(DeviceUser).filter(DeviceUser.id == message["user_id"]).first()
            if user:
                user.username = message["username"]
                user.role = message["role"]
                db.commit()
                logger.info(f"Updated device user {message['user_id']}")
            else:
                self._handle_user_created(message)
    
    def _handle_user_deleted(self, message: dict):
        """Handle USER_DELETED event"""
        with self.SessionLocal() as db:
          
            from .schemas import Device
            db.query(Device).filter(Device.device_user_id == message["user_id"]).update({"device_user_id": None})
           
            db.query(DeviceUser).filter(DeviceUser.id == message["user_id"]).delete()
            db.commit()
            logger.info(f"Deleted device user {message['user_id']}")
    
    def start(self):
        """Start consuming messages"""
        self.rabbitmq_client.connect()
        self.rabbitmq_client.declare_exchange("sync_events", "fanout")
        self.rabbitmq_client.declare_queue("device_service_sync_queue")
        self.rabbitmq_client.bind_queue_to_exchange("device_service_sync_queue", "sync_events")
        logger.info("Device sync consumer started")
        self.rabbitmq_client.consume("device_service_sync_queue", self.handle_message)