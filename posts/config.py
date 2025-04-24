import os

class Config:
    GRPC_PORT = int(os.environ.get('GRPC_PORT', 50051))
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@posts-db:5432/posts_service')
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')