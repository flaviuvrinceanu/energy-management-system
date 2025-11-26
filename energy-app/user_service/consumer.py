import sys
sys.path.append('/app')
from shared.rabbitmq_utils import RabbitMQClient
from .schemas import User, Role
import logging

logger = logging.getLogger(__name__)

class UserSyncConsumer:
    def __init__(self, SessionLocal):
        self.SessionLocal = SessionLocal
        self.rabbitmq_client = RabbitMQClient()
    
    def handle_message(self, message: dict):
        """Handle incoming sync events"""
        event_type = message.get("event_type")
        
        if event_type == "USER_CREATED":
            self.handle_user_created(message)
        elif event_type == "USER_UPDATED":
            self.handle_user_updated(message)
        elif event_type == "USER_DELETED":
            self.handle_user_deleted(message)
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    def handle_user_created(self, message: dict):
        """Handle USER_CREATED event"""
        with self.SessionLocal() as db:
            existing = db.query(User).filter(User.id == message["user_id"]).first()
            if not existing:
                user = User(
                    id=message["user_id"],
                    username=message["username"],
                    role=Role(message["role"])
                )
                db.add(user)
                db.commit()
                logger.info(f"Created user {message['user_id']}")
            else:
                logger.info(f"User {message['user_id']} already exists")
    
    def handle_user_updated(self, message: dict):
        """Handle USER_UPDATED event"""
        with self.SessionLocal() as db:
            user = db.query(User).filter(User.id == message["user_id"]).first()
            if user:
                user.username = message["username"]
                user.role = Role(message["role"])
                db.commit()
                logger.info(f"Updated user {message['user_id']}")
            else:
                
                self.handle_user_created(message)
    
    def handle_user_deleted(self, message: dict):
        """Handle USER_DELETED event"""
        with self.SessionLocal() as db:
            db.query(User).filter(User.id == message["user_id"]).delete()
            db.commit()
            logger.info(f"Deleted user {message['user_id']}")
    
    def start(self):
        """Start consuming messages"""
        self.rabbitmq_client.connect()
        self.rabbitmq_client.declare_exchange("sync_events", "fanout")
        self.rabbitmq_client.declare_queue("user_service_sync_queue")
        self.rabbitmq_client.bind_queue_to_exchange("user_service_sync_queue", "sync_events")
        logger.info("User sync consumer started")
        self.rabbitmq_client.consume("user_service_sync_queue", self.handle_message)