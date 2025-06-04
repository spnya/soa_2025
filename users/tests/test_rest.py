import pytest
import sys
import os
import json
os.environ['TESTING'] = '1'

# Отключаем Kafka в тестах:
os.environ["DISABLE_KAFKA"] = "1"

# Добавляем в sys.path корень приложения (папку “users”)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from models import db

# Патчим event_producer, чтобы send_user_registration_event сразу возвращал True
import routes.user_routes as user_routes
class _DummyProducer:
    def send_user_registration_event(self, user_id): return True
user_routes.event_producer = _DummyProducer()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.session.remove()
            db.drop_all()


def test_register_user(client):
    response = client.post(
        "/api/users/register",
        json={
            "username": "restuser",
            "password": "restpassword",
            "email": "rest@example.com",
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["username"] == "restuser"
    assert data["email"] == "rest@example.com"
    assert "id" in data


def test_login_user(client):
    # Сначала регистрируем нового пользователя
    client.post(
        "/api/users/register",
        json={
            "username": "loginuser",
            "password": "loginpassword",
            "email": "login@example.com",
        },
    )

    # Затем пробуем войти
    response = client.post(
        "/api/users/login",
        json={"username": "loginuser", "password": "loginpassword"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
    assert data["username"] == "loginuser"


def test_get_profile(client):
    # Регистрация
    client.post(
        "/api/users/register",
        json={
            "username": "profileuser",
            "password": "profilepass",
            "email": "profile@example.com",
        },
    )

    # Логин
    login_resp = client.post(
        "/api/users/login",
        json={"username": "profileuser", "password": "profilepass"},
    )
    token = login_resp.get_json()["access_token"]

    # Получение профиля по JWT
    response = client.get(
        "/api/users/profile", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == "profileuser"
    assert data["email"] == "profile@example.com"
