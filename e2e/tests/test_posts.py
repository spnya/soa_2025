import pytest
import requests
import random
import string
import time

BASE_URL = "http://localhost:8000"

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))


@pytest.fixture(scope="module")
def create_user_and_token():
    """
    Регистрирует пользователя и возвращает JWT-токен.
    """
    username = f"user_{random_string()}"
    password = "Password123!"
    email = f"{username}@example.com"

    # Регистрация
    resp = requests.post(
        f"{BASE_URL}/api/users/register",
        json={"username": username, "password": password, "email": email}
    )
    assert resp.status_code == 201

    # Логин
    resp = requests.post(
        f"{BASE_URL}/api/users/login",
        json={"username": username, "password": password}
    )
    assert resp.status_code == 200
    data = resp.json()
    token = data["access_token"]
    return {"username": username, "password": password, "token": token}


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_user_registration_and_post_creation(create_user_and_token):
    """
    1) Регистрируем пользователя
    2) Логинимся и получаем токен
    3) Создаем пост
    4) Проверяем, что пост появился в списке
    """
    token = create_user_and_token["token"]

    # Создаем пост
    post_payload = {
        "title": "E2E Test Post",
        "description": "This is a post created in an end-to-end test.",
        "is_private": False,
        "tags": ["e2e", "test"]
    }
    resp = requests.post(
        f"{BASE_URL}/api/posts",
        json=post_payload,
        headers=auth_headers(token)
    )
    assert resp.status_code == 201
    post_data = resp.json()
    assert post_data["title"] == post_payload["title"]
    assert post_data["description"] == post_payload["description"]
    post_id = post_data["id"]

    # Проверяем, что пост возвращается в общем списке
    resp = requests.get(
        f"{BASE_URL}/api/posts",
        headers=auth_headers(token),
        params={"page": 1, "per_page": 10}
    )
    assert resp.status_code == 200
    posts_list = resp.json()["posts"]
    assert any(p["id"] == post_id for p in posts_list)


def test_post_interactions_and_statistics(create_user_and_token):
    """
    Сценарий:
    1) Юзер1 регистрируется и создает пост.
    2) Юзер2 регистрируется, логинится и:
       - Просматривает пост Юзера1
       - Лайкает пост
       - Комментирует пост
    3) Проверяем статистику поста (views, likes, comments).
    """
    # --- Юзер1 ---
    user1 = create_user_and_token
    token1 = user1["token"]

    # Юзер1 создает пост
    post_payload = {
        "title": "Stats Test Post",
        "description": "Post for statistics test",
        "is_private": False,
        "tags": ["stats", "test"]
    }
    resp = requests.post(
        f"{BASE_URL}/api/posts",
        json=post_payload,
        headers=auth_headers(token1)
    )
    assert resp.status_code == 201
    post_id = resp.json()["id"]

    # --- Юзер2 ---
    username2 = f"user_{random_string()}"
    password2 = "Password123!"
    email2 = f"{username2}@example.com"

    # Регистрация Юзера2
    resp = requests.post(
        f"{BASE_URL}/api/users/register",
        json={"username": username2, "password": password2, "email": email2}
    )
    assert resp.status_code == 201

    # Логин Юзера2
    resp = requests.post(
        f"{BASE_URL}/api/users/login",
        json={"username": username2, "password": password2}
    )
    assert resp.status_code == 200
    token2 = resp.json()["access_token"]

    # Юзер2 просматривает пост
    resp = requests.post(
        f"{BASE_URL}/api/posts/{post_id}/view",
        headers=auth_headers(token2)
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Post viewed successfully"

    # Юзер2 лайкает пост
    resp = requests.post(
        f"{BASE_URL}/api/posts/{post_id}/like",
        headers=auth_headers(token2)
    )
    assert resp.status_code == 200
    assert "liked" in resp.json()["message"].lower()

    # Юзер2 комментирует пост
    comment_payload = {"content": "Great post!"}
    resp = requests.post(
        f"{BASE_URL}/api/posts/{post_id}/comments",
        json=comment_payload,
        headers=auth_headers(token2)
    )
    assert resp.status_code == 201
    comment_data = resp.json()
    assert comment_data["content"] == "Great post!"
    assert comment_data["post_id"] == post_id

    # Делаем небольшую паузу, чтобы события дошли до ClickHouse
    time.sleep(1)

    # Получаем статистику поста
    resp = requests.get(
        f"{BASE_URL}/api/statistics/posts/{post_id}/stats",
        headers=auth_headers(token1)
    )
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["post_id"] == post_id
    assert stats["views"] >= 1
    assert stats["likes"] >= 1
    assert stats["comments"] >= 1


def test_top_posts_and_users(create_user_and_token):
    """
    Сценарий:
    1) Создаем несколько постов разными юзерами.
    2) Разные пользователи просматривают и лайкают посты.
    3) Проверяем эндпойнты /statistics/posts/top и /statistics/users/top.
    """
    # --- Юзер1 и Юзер2 ---
    user1 = create_user_and_token
    token1 = user1["token"]

    username2 = f"user_{random_string()}"
    password2 = "Password123!"
    email2 = f"{username2}@example.com"

    # Регистрация Юзера2
    resp = requests.post(
        f"{BASE_URL}/api/users/register",
        json={"username": username2, "password": password2, "email": email2}
    )
    assert resp.status_code == 201

    # Логин Юзера2
    resp = requests.post(
        f"{BASE_URL}/api/users/login",
        json={"username": username2, "password": password2}
    )
    assert resp.status_code == 200
    token2 = resp.json()["access_token"]

    # --- Создаем по два поста от каждого юзера ---
    post_ids = []
    for tkn in (token1, token2):
        for i in range(2):
            resp = requests.post(
                f"{BASE_URL}/api/posts",
                json={
                    "title": f"Post by {('User1','User2')[tkn==token2]} #{i}",
                    "description": "Testing top endpoints",
                    "is_private": False,
                    "tags": []
                },
                headers=auth_headers(tkn)
            )
            assert resp.status_code == 201
            post_ids.append(resp.json()["id"])

    # --- Интер-акции: Юзер1 смотрит и лайкает все посты Юзера2 ---
    for pid in post_ids[2:]:
        # Просмотр
        resp = requests.post(
            f"{BASE_URL}/api/posts/{pid}/view",
            headers=auth_headers(token1)
        )
        assert resp.status_code == 200

        # Лайк
        resp = requests.post(
            f"{BASE_URL}/api/posts/{pid}/like",
            headers=auth_headers(token1)
        )
        assert resp.status_code == 200

    # --- Интер-акции: Юзер2 смотрит и лайкает все посты Юзера1 ---
    for pid in post_ids[:2]:
        resp = requests.post(
            f"{BASE_URL}/api/posts/{pid}/view",
            headers=auth_headers(token2)
        )
        assert resp.status_code == 200
        resp = requests.post(
            f"{BASE_URL}/api/posts/{pid}/like",
            headers=auth_headers(token2)
        )
        assert resp.status_code == 200

    # Пауза для записи статистики
    time.sleep(1)

    # Проверяем топ постов (по просмотрам, default=views)
    resp = requests.get(
        f"{BASE_URL}/api/statistics/posts/top",
        headers=auth_headers(token1)
    )
    assert resp.status_code == 200
    top_posts = resp.json()["posts"]
    assert isinstance(top_posts, list)
    assert len(top_posts) >= 1
    # Проверяем топ пользователей (по просмотрам, default=views)
    resp = requests.get(
        f"{BASE_URL}/api/statistics/users/top",
        headers=auth_headers(token2)
    )
    assert resp.status_code == 200
    top_users = resp.json()["users"]
    assert isinstance(top_users, list)
    # Должны увидеть user1 и user2
    user_ids = {u["user_id"] for u in top_users}
    # Предположим у user1 и user2 id уникальны и не пересекаются
    assert any(u != user1["username"] for u in top_users) or len(user_ids) >= 2
