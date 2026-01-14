import sys
sys.path.append('/app')
from shared.rabbitmq_utils import RabbitMQClient
import os
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadBalancer:
    def __init__(self):
        self.rabbitmq_input = RabbitMQClient()
        self.rabbitmq_output = RabbitMQClient()
        
       
        self.num_replicas = int(os.getenv("NUM_REPLICAS", "3"))
        self.strategy = os.getenv("LOAD_STRATEGY", "round-robin")  # round robin or consistent hash
        
       
        self.current_replica = 0
        
        logger.info(f"Load Balancer initialized with {self.num_replicas} replicas, strategy={self.strategy}")
    
    def get_target_queue(self, message: dict) -> str:
        """
        Determine target ingest queue based on load balancing strategy
        """
        if self.strategy == "consistent-hash":
            
            device_id = message.get("device_id", "")
            hash_value = int(hashlib.md5(device_id.encode()).hexdigest(), 16)
            replica_id = (hash_value % self.num_replicas) + 1
            return f"ingest_queue_{replica_id}"
        
        else:  
            self.current_replica = (self.current_replica % self.num_replicas) + 1
            return f"ingest_queue_{self.current_replica}"
    
    def handle_message(self, message: dict):
        """
        Handle incoming message from device_data_queue and forward to appropriate ingest queue
        """
        try:
            target_queue = self.get_target_queue(message)
            
           
            self.rabbitmq_output.publish(target_queue, message)
            
            device_id = message.get("device_id", "unknown")
            logger.info(f"Forwarded message from device {device_id} to {target_queue}")
        
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def start(self):
        """
        Start load balancer: consume from device_data_queue and distribute to ingest queues
        """
        try:
            
            self.rabbitmq_input.connect()
            self.rabbitmq_input.declare_queue("device_data_queue")
            
            
            self.rabbitmq_output.connect()
            for i in range(1, self.num_replicas + 1):
                queue_name = f"ingest_queue_{i}"
                self.rabbitmq_output.declare_queue(queue_name)
                logger.info(f"Declared queue: {queue_name}")
            
            logger.info("Load Balancer started, consuming from device_data_queue")
            
            
            self.rabbitmq_input.consume("device_data_queue", self.handle_message)
        
        except KeyboardInterrupt:
            logger.info("Load Balancer stopped")
        except Exception as e:
            logger.error(f"Error in Load Balancer: {e}")
        finally:
            self.rabbitmq_input.close()
            self.rabbitmq_output.close()


if __name__ == "__main__":
    balancer = LoadBalancer()
    balancer.start()
