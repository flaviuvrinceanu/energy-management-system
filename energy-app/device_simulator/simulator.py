
import time
import json
import random
import argparse
import os
from datetime import datetime, timezone
from typing import Dict, Any
import pika
import sys

class DeviceSimulator:
    def __init__(self, device_id: str, rabbitmq_config: Dict[str, Any], interval_seconds: int = 600):
        """
        Initialize the device simulator.
        
        Args:
            device_id: Unique identifier for the simulated device
            rabbitmq_config: Dictionary with RabbitMQ connection parameters
            interval_seconds: Interval between readings in seconds (default 600 = 10 minutes)
        """
        self.device_id = device_id
        self.rabbitmq_config = rabbitmq_config
        self.interval_seconds = interval_seconds
        self.connection = None
        self.channel = None
        
    def connect_rabbitmq(self):
        """Establish connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                self.rabbitmq_config['username'],
                self.rabbitmq_config['password']
            )
            parameters = pika.ConnectionParameters(
                host=self.rabbitmq_config['host'],
                port=self.rabbitmq_config['port'],
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='device_data_queue', durable=True)
            print(f" Connected to RabbitMQ at {self.rabbitmq_config['host']}:{self.rabbitmq_config['port']}")
        except Exception as e:
            print(f" Failed to connect to RabbitMQ: {e}")
            sys.exit(1)
    
    def generate_reading(self) -> float:
        """
        Generate energy consumption reading (kWh).
        
        Patterns:
        - Night (22:00-06:00): 0.05-0.15 kWh 
        - Morning (06:00-09:00): 0.15-0.35 kWh 
        - Day (09:00-17:00): 0.10-0.25 kWh 
        - Evening (17:00-22:00): 0.25-0.50 kWh 
        
        """
        current_hour = datetime.now().hour
        
        # Base consumption based on time of day
        if 22 <= current_hour or current_hour < 6:  #Night
            base = 0.10
            variance = 0.05
        elif 6 <= current_hour < 9:  #Morning
            base = 0.25
            variance = 0.10
        elif 9 <= current_hour < 17:  #Day
            base = 0.17
            variance = 0.08
        else:  #Evening
            base = 0.37
            variance = 0.13
        
        #random fluctuation
        reading = base + random.uniform(-variance, variance)
        return max(0.01, round(reading, 4))  #non-negative, round to 4 decimals
    
    def send_reading(self, reading: float):
        message = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "device_id": self.device_id,
            "measurement_value": reading
        }
        
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key='device_data_queue',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  
                )
            )
            print(f"[{message['timestamp']}] Device {self.device_id}: {reading} kWh sent")
        except Exception as e:
            print(f" Failed to send reading: {e}")
          
            self.connect_rabbitmq()
    
    def run(self):
        """Main simulation loop"""
        print(f"\n=== Device Simulator Started ===")
        print(f"Device ID: {self.device_id}")
        print(f"Interval: {self.interval_seconds} seconds ({self.interval_seconds/60} minutes)")
        print(f"Queue: device_data_queue")
        print(f"================================\n")
        
        self.connect_rabbitmq()
        
        try:
            while True:
                reading = self.generate_reading()
                self.send_reading(reading)
                time.sleep(self.interval_seconds)
        except KeyboardInterrupt:
            print("\n\n=== Simulator Stopped ===")
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                print(" RabbitMQ connection closed")

def main():
    parser = argparse.ArgumentParser(description='Device Data Simulator')
    parser.add_argument('--device-id', type=str, help='Device ID to simulate')
    parser.add_argument('--interval', type=int, default=600, help='Interval between readings in seconds (default: 600)')
    parser.add_argument('--rabbitmq-host', type=str, default='localhost', help='RabbitMQ host')
    parser.add_argument('--rabbitmq-port', type=int, default=5672, help='RabbitMQ port')
    parser.add_argument('--rabbitmq-user', type=str, default='guest', help='RabbitMQ username')
    parser.add_argument('--rabbitmq-pass', type=str, default='guest', help='RabbitMQ password')
    
    args = parser.parse_args()
    
   
    device_id = args.device_id or os.getenv('DEVICE_ID')
    if not device_id:
        print("Error: --device-id is required (or set DEVICE_ID environment variable)")
        sys.exit(1)
    
    rabbitmq_config = {
        'host': args.rabbitmq_host or os.getenv('RABBITMQ_HOST', 'localhost'),
        'port': args.rabbitmq_port or int(os.getenv('RABBITMQ_PORT', '5672')),
        'username': args.rabbitmq_user or os.getenv('RABBITMQ_USER', 'guest'),
        'password': args.rabbitmq_pass or os.getenv('RABBITMQ_PASS', 'guest'),
    }
    
    simulator = DeviceSimulator(device_id, rabbitmq_config, args.interval)
    simulator.run()

if __name__ == "__main__":
    main()