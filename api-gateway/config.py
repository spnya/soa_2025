import os

class Config:
    USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://user-service:5000')
    POSTS_SERVICE_URL = os.environ.get('POSTS_SERVICE_URL', 'posts-service')
    POSTS_SERVICE_PORT = os.environ.get('POSTS_SERVICE_PORT', '50051')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your_super_secret_key_change_in_production')