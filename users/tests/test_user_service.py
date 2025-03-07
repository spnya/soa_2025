import pytest
import sys
import os
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, User
from services.user_service import UserService


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


def test_create_user(client):
    """Тест создания пользователя"""
    with app.app_context():
        user = UserService.create_user(
            username='testuser',
            password='testpassword',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )

        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.check_password('testpassword')


def test_get_user_by_username(client):
    """Тест получения пользователя по логину"""
    with app.app_context():
        UserService.create_user(
            username='testuser',
            password='testpassword',
            email='test@example.com'
        )

        user = UserService.get_user_by_username('testuser')
        assert user is not None
        assert user.username == 'testuser'

        nonexistent_user = UserService.get_user_by_username('nonexistent')
        assert nonexistent_user is None


def test_update_user(client):
    """Тест обновления данных пользователя"""
    with app.app_context():
        user = UserService.create_user(
            username='testuser',
            password='testpassword',
            email='test@example.com'
        )

        created_at = user.created_at

        import time
        time.sleep(0.1)

        updated_user = UserService.update_user(user, {
            'first_name': 'Updated',
            'last_name': 'User',
            'phone_number': '+1234567890',
            'birth_date': datetime.date(1990, 1, 1)
        })

        assert updated_user.first_name == 'Updated'
        assert updated_user.last_name == 'User'
        assert updated_user.phone_number == '+1234567890'
        assert updated_user.birth_date == datetime.date(1990, 1, 1)

        assert updated_user.created_at == created_at
        assert updated_user.updated_at > created_at
