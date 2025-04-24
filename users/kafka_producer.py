from kafka import KafkaProducer
import json
import logging
from datetime import datetime

class EventProducer:
    def __init__(self, bootstrap_servers):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                api_version=(0, 10)
            )
            logging.info(f"Kafka producer initialized with bootstrap servers: {bootstrap_servers}")
        except Exception as e:
            logging.error(f"Failed to initialize Kafka producer: {str(e)}")
            self.producer = None

    def send_event(self, topic, event_data):
        """Send an event to the specified Kafka topic"""
        if not self.producer:
            logging.error(f"Cannot send message to topic {topic}: Kafka producer not initialized")
            return False

        try:
            future = self.producer.send(topic, event_data)
            # Wait for the send to complete to catch any errors
            record_metadata = future.get(timeout=10)
            logging.info(f"Event sent to {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
            return True
        except Exception as e:
            logging.error(f"Error sending event to topic {topic}: {str(e)}")
            return False

    def send_user_registration_event(self, user_id):
        """Send a user registration event"""
        event_data = {
            'event_type': 'user_registration',
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        return self.send_event('user_registrations', event_data)

    def close(self):
        """Close the Kafka producer"""
        if self.producer:
            self.producer.close()
            logging.info("Kafka producer closed")