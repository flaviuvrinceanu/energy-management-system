import pika
import json
import os
from typing import Callable, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self):
        self.host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        self.port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.username = os.getenv("RABBITMQ_USER", "guest")
        self.password = os.getenv("RABBITMQ_PASS", "guest")
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Establish connection to RabbitMQ"""
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
    
    def declare_queue(self, queue_name: str, durable: bool = True):
        """Declare a queue"""
        if not self.channel:
            self.connect()
        self.channel.queue_declare(queue=queue_name, durable=durable)
        logger.info(f"Queue '{queue_name}' declared")
    
    def declare_exchange(self, exchange_name: str, exchange_type: str = 'fanout', durable: bool = True):
        """Declare an exchange"""
        if not self.channel:
            self.connect()
        self.channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=durable)
        logger.info(f"Exchange '{exchange_name}' (type={exchange_type}) declared")
    
    def bind_queue_to_exchange(self, queue_name: str, exchange_name: str, routing_key: str = ''):
        """Bind a queue to an exchange"""
        if not self.channel:
            self.connect()
        self.channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
        logger.info(f"Queue '{queue_name}' bound to exchange '{exchange_name}'")
    
    def publish(self, queue_name: str, message: Dict[Any, Any], exchange: str = ''):
        """Publish a message to a queue or exchange"""
        if not self.channel:
            self.connect()
        routing_key = '' if exchange else queue_name
        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  
            )
        )
        target = f"exchange '{exchange}'" if exchange else f"queue '{queue_name}'"
        logger.info(f"Published to {target}: {message}")
    
    def consume(self, queue_name: str, callback: Callable):
        """Start consuming messages from a queue"""
        if not self.channel:
            self.connect()
        
        def wrapped_callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                callback(message)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=wrapped_callback,
            auto_ack=False
        )
        logger.info(f"Started consuming from '{queue_name}'")
        self.channel.start_consuming()
    
    def close(self):
        """Close the connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")