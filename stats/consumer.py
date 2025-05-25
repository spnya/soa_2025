from kafka import KafkaConsumer
import json
import logging
from datetime import datetime
from typing import Dict, Any
import threading
from clickhouse_driver import Client
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatisticsEventConsumer:
    def __init__(self, bootstrap_servers: str, clickhouse_host: str = 'localhost', clickhouse_port: int = 9000):
        """
        Initialize the statistics event consumer
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            clickhouse_host: ClickHouse host
            clickhouse_port: ClickHouse port
        """
        self.bootstrap_servers = bootstrap_servers
        self.clickhouse_client = Client(
            host=clickhouse_host,
            port=clickhouse_port,
            database='statistics'
        )
        self.consumer = None
        self.running = False
        
        # Initialize ClickHouse database and tables
        self._init_clickhouse()
        
    def _init_clickhouse(self):
        """Initialize ClickHouse database and tables"""
        try:
            # Create database if not exists
            self.clickhouse_client.execute("CREATE DATABASE IF NOT EXISTS statistics")
            
            # Create events table
            self.clickhouse_client.execute("""
                CREATE TABLE IF NOT EXISTS statistics.events (
                    event_id UUID DEFAULT generateUUIDv4(),
                    event_type String,
                    user_id UInt64,
                    post_id Nullable(UInt64),
                    comment_id Nullable(UInt64),
                    timestamp DateTime64(3, 'UTC'),
                    date Date DEFAULT toDate(timestamp)
                ) ENGINE = MergeTree()
                PARTITION BY date
                ORDER BY (event_type, timestamp, user_id)
                SETTINGS index_granularity = 8192
            """)
            
            # Create materialized views for aggregated statistics
            self._create_materialized_views()
            
            logger.info("ClickHouse database and tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ClickHouse: {str(e)}")
            raise
    
    def _create_materialized_views(self):
        """Create materialized views for aggregated statistics"""
        
        # Daily post statistics
        self.clickhouse_client.execute("""
            CREATE TABLE IF NOT EXISTS statistics.daily_post_stats (
                post_id UInt64,
                date Date,
                views UInt64,
                likes UInt64,
                comments UInt64
            ) ENGINE = SummingMergeTree()
            PARTITION BY date
            ORDER BY (post_id, date)
        """)
        
        self.clickhouse_client.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS statistics.daily_post_stats_mv
            TO statistics.daily_post_stats
            AS SELECT
                post_id,
                date,
                countIf(event_type = 'post_view') as views,
                countIf(event_type = 'post_like') as likes,
                countIf(event_type = 'post_comment') as comments
            FROM statistics.events
            WHERE post_id IS NOT NULL
            GROUP BY post_id, date
        """)
        
        # User statistics
        self.clickhouse_client.execute("""
            CREATE TABLE IF NOT EXISTS statistics.user_stats (
                user_id UInt64,
                views UInt64,
                likes UInt64,
                comments UInt64
            ) ENGINE = SummingMergeTree()
            ORDER BY user_id
        """)
        
        self.clickhouse_client.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS statistics.user_stats_mv
            TO statistics.user_stats
            AS SELECT
                user_id,
                countIf(event_type = 'post_view') as views,
                countIf(event_type = 'post_like') as likes,
                countIf(event_type = 'post_comment') as comments
            FROM statistics.events
            GROUP BY user_id
        """)
        
        # Post total statistics
        self.clickhouse_client.execute("""
            CREATE TABLE IF NOT EXISTS statistics.post_stats (
                post_id UInt64,
                views UInt64,
                likes UInt64,
                comments UInt64
            ) ENGINE = SummingMergeTree()
            ORDER BY post_id
        """)
        
        self.clickhouse_client.execute("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS statistics.post_stats_mv
            TO statistics.post_stats
            AS SELECT
                post_id,
                countIf(event_type = 'post_view') as views,
                countIf(event_type = 'post_like') as likes,
                countIf(event_type = 'post_comment') as comments
            FROM statistics.events
            WHERE post_id IS NOT NULL
            GROUP BY post_id
        """)
    
    def _init_consumer(self):
        """Initialize Kafka consumer"""
        try:
            self.consumer = KafkaConsumer(
                'user_registrations',
                'post_likes', 
                'post_views',
                'post_comments',
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='statistics_consumer_group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=1000,
                api_version=(0, 10)
            )
            logger.info("Kafka consumer initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {str(e)}")
            return False
    
    def _process_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process a single event and save to ClickHouse
        
        Args:
            event_data: Event data from Kafka
            
        Returns:
            bool: True if processed successfully, False otherwise
        """
        try:
            event_type = event_data.get('event_type')
            user_id = event_data.get('user_id')
            timestamp = event_data.get('timestamp')
            
            if not all([event_type, user_id, timestamp]):
                logger.warning(f"Missing required fields in event: {event_data}")
                return False
            
            # Parse timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                dt = datetime.fromisoformat(timestamp)
            
            # Prepare data for insertion
            insert_data = {
                'event_type': event_type,
                'user_id': user_id,
                'post_id': event_data.get('post_id'),
                'comment_id': event_data.get('comment_id'),
                'timestamp': dt
            }
            
            # Insert into ClickHouse
            self.clickhouse_client.execute(
                """
                INSERT INTO statistics.events 
                (event_type, user_id, post_id, comment_id, timestamp) 
                VALUES
                """,
                [insert_data]
            )
            
            logger.debug(f"Event processed successfully: {event_type} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process event {event_data}: {str(e)}")
            return False
    
    def start_consuming(self):
        """Start consuming events from Kafka"""
        if not self._init_consumer():
            logger.error("Failed to initialize consumer, cannot start consuming")
            return
        
        self.running = True
        logger.info("Starting to consume events from Kafka...")
        
        try:
            while self.running:
                try:
                    message_pack = self.consumer.poll(timeout_ms=1000)
                    
                    for topic_partition, messages in message_pack.items():
                        for message in messages:
                            try:
                                event_data = message.value
                                logger.debug(f"Received event from topic {message.topic}: {event_data}")
                                
                                success = self._process_event(event_data)
                                if success:
                                    logger.info(f"Successfully processed {event_data.get('event_type')} event")
                                else:
                                    logger.warning(f"Failed to process event: {event_data}")
                                    
                            except Exception as e:
                                logger.error(f"Error processing message from {message.topic}: {str(e)}")
                                continue
                
                except Exception as e:
                    logger.error(f"Error during polling: {str(e)}")
                    time.sleep(5)  # Wait before retrying
                    
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error in consumer: {str(e)}")
        finally:
            self.stop_consuming()
    
    def stop_consuming(self):
        """Stop consuming events"""
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")
    
    def get_connection_status(self) -> Dict[str, bool]:
        """Check connection status to Kafka and ClickHouse"""
        status = {
            'kafka': False,
            'clickhouse': False
        }
        
        # Check Kafka connection
        try:
            test_consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                consumer_timeout_ms=5000,
                api_version=(0, 10)
            )
            test_consumer.close()
            status['kafka'] = True
        except Exception as e:
            logger.error(f"Kafka connection failed: {str(e)}")
        
        # Check ClickHouse connection
        try:
            self.clickhouse_client.execute("SELECT 1")
            status['clickhouse'] = True
        except Exception as e:
            logger.error(f"ClickHouse connection failed: {str(e)}")
        
        return status


def main():
    """Main function to run the consumer"""
    import os
    
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    clickhouse_host = os.getenv('CLICKHOUSE_HOST', 'clickhouse')
    clickhouse_port = int(os.getenv('CLICKHOUSE_PORT', '9000'))
    
    consumer = StatisticsEventConsumer(
        bootstrap_servers=bootstrap_servers,
        clickhouse_host=clickhouse_host,
        clickhouse_port=clickhouse_port
    )
    
    # Check connections before starting
    status = consumer.get_connection_status()
    if not all(status.values()):
        logger.error(f"Connection check failed: {status}")
        return
    
    logger.info("All connections successful, starting consumer...")
    
    try:
        consumer.start_consuming()
    except Exception as e:
        logger.error(f"Failed to start consumer: {str(e)}")
    finally:
        consumer.stop_consuming()


if __name__ == "__main__":
    main()