import os

class Config:
    USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://user-service:5000')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your_super_secret_key_change_in_production')