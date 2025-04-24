import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')
    if os.environ.get('TESTING', False):
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory'
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                                                 'postgresql://postgres:postgres@localhost:5432/user_service')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your_super_secret_key_change_in_production')
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

