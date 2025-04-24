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
            record_metadata = future.get(timeout=10)
            logging.info(f"Event sent to {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
            return True
        except Exception as e:
            logging.error(f"Error sending event to topic {topic}: {str(e)}")
            return False

    def send_view_event(self, user_id, post_id):
        """Send a post view event"""
        event_data = {
            'event_type': 'post_view',
            'user_id': user_id,
            'post_id': post_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        return self.send_event('post_views', event_data)

    def send_like_event(self, user_id, post_id):
        """Send a post like event"""
        event_data = {
            'event_type': 'post_like',
            'user_id': user_id,
            'post_id': post_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        return self.send_event('post_likes', event_data)

    def send_comment_event(self, user_id, post_id, comment_id):
        """Send a post comment event"""
        event_data = {
            'event_type': 'post_comment',
            'user_id': user_id,
            'post_id': post_id,
            'comment_id': comment_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        return self.send_event('post_comments', event_data)

    def close(self):
        """Close the Kafka producer"""
        if self.producer:
            self.producer.close()
            logging.info("Kafka producer closed")