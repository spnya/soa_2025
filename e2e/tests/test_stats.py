import requests
import time
import pytest

API_URL = "http://localhost:8000"

@pytest.fixture(scope="module")
def registered_user():
    r = requests.post(f"{API_URL}/api/users/register", json={
        "username": "stat_user",
        "password": "Stat1234!",
        "email": "stat_user@example.com"
    })
    assert r.status_code == 201 or r.status_code == 409  # 409 = уже существует

    login = requests.post(f"{API_URL}/api/users/login", json={
        "username": "stat_user",
        "password": "Stat1234!"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_statistics_flow(registered_user):
    # 1. Создаём пост
    post = requests.post(f"{API_URL}/api/posts", json={
        "title": "Stat Post",
        "description": "Stat test"
    }, headers=registered_user)
    assert post.status_code == 201
    post_id = post.json()["id"]

    # 2. Регистрируем события
    for _ in range(3):
        assert requests.post(f"{API_URL}/api/posts/{post_id}/view", headers=registered_user).status_code == 200
    for _ in range(2):
        assert requests.post(f"{API_URL}/api/posts/{post_id}/like", headers=registered_user).status_code == 200
    assert requests.post(f"{API_URL}/api/posts/{post_id}/comments", json={"content": "Nice!"}, headers=registered_user).status_code == 201

    # Даем Kafka немного времени обработать события
    time.sleep(2)

    # 3. Проверяем агрегированную статистику
    stats = requests.get(f"{API_URL}/api/statistics/posts/{post_id}/stats", headers=registered_user)
    assert stats.status_code == 200
    data = stats.json()
    assert data["post_id"] == post_id
    assert data["views"] >= 1
    assert data["likes"] >= 0
    assert data["comments"] >= 1

    # 4. Проверяем динамику
    dyn_views = requests.get(f"{API_URL}/api/statistics/posts/{post_id}/dynamics/views", headers=registered_user)
    assert dyn_views.status_code == 200
    assert len(dyn_views.json()["dynamics"]) >= 1
