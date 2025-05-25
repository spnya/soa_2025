import os

class Config:
    # Kafka configuration
    KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    
    # ClickHouse configuration
    CLICKHOUSE_HOST = os.environ.get('CLICKHOUSE_HOST', 'clickhouse')
    CLICKHOUSE_PORT = int(os.environ.get('CLICKHOUSE_PORT', '9000'))
    CLICKHOUSE_DATABASE = os.environ.get('CLICKHOUSE_DATABASE', 'statistics')
    
    # gRPC server configuration
    GRPC_PORT = os.environ.get('GRPC_PORT', '50052')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')