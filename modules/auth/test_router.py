import pytest
from httpx import AsyncClient
from modules.auth.manager import AuthManager
from modules.auth.utils import get_current_user
from main import app

@pytest.mark.asyncio
async def test_register_success(monkeypatch):
    async def mock_register(user):
        return {"id": 1, "email": user.email, "first_name": user.first_name, "last_name": user.last_name, "is_admin": False, "is_doctor": False}
    monkeypatch.setattr(AuthManager, "register", mock_register)
    user = {
        "email": "test@example.com",
        "password": "strongpassword",
        "first_name": "Test",
        "last_name": "User",
        "is_admin": False
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/auth/register", json=user)
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == user["email"]

@pytest.mark.asyncio
async def test_register_duplicate_email(monkeypatch):
    async def mock_register(user):
        raise ValueError("Email already registered")
    monkeypatch.setattr(AuthManager, "register", mock_register)
    user = {
        "email": "test@example.com",
        "password": "strongpassword",
        "first_name": "Test",
        "last_name": "User",
        "is_admin": False
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/auth/register", json=user)
    assert resp.status_code == 400
    assert resp.json()["error"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_success(monkeypatch):
    async def mock_login(email, password):
        return "token123"
    monkeypatch.setattr(AuthManager, "login", mock_login)
    data = {"username": "test@example.com", "password": "strongpassword"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/auth/login", data=data)
    assert resp.status_code == 200
    assert resp.json()["data"]["access_token"] == "token123"

@pytest.mark.asyncio
async def test_login_invalid(monkeypatch):
    async def mock_login(email, password):
        raise ValueError("Invalid email or password")
    monkeypatch.setattr(AuthManager, "login", mock_login)
    data = {"username": "test@example.com", "password": "wrongpass"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/auth/login", data=data)
    assert resp.status_code == 401
    assert resp.json()["error"] == "Invalid email or password"

@pytest.mark.asyncio
async def test_get_me_success(monkeypatch):
    async def mock_get_current_user():
        return {"id": 1, "email": "test@example.com", "first_name": "Test", "last_name": "User", "is_admin": False, "is_doctor": False}
    app.dependency_overrides[get_current_user] = mock_get_current_user
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == "test@example.com"
    app.dependency_overrides = {}

