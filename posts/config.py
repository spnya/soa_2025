import os

class Config:
    GRPC_PORT = int(os.environ.get('GRPC_PORT', 50051))
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@posts-db:5432/posts_service')
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')