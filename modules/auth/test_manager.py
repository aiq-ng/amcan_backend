import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from .manager import AuthManager
from .models import UserCreate

@pytest_asyncio.fixture
def user_data():
    return UserCreate(
        email="test@example.com",
        password="strongpassword",
        first_name="Test",
        last_name="User",
        is_admin=False
    )

@pytest.mark.asyncio
@patch("modules.auth.manager.db.get_connection")
@patch("modules.auth.manager.hash_password", return_value="hashedpass")
async def test_register_success(mock_hash, mock_get_conn, user_data):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.side_effect = [None, {"id": 1, "email": user_data.email, "first_name": user_data.first_name, "last_name": user_data.last_name, "is_admin": False, "is_doctor": False}]
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await AuthManager.register(user_data)
    assert result["email"] == user_data.email
    assert result["first_name"] == user_data.first_name
    assert result["is_admin"] is False

@pytest.mark.asyncio
@patch("modules.auth.manager.db.get_connection")
async def test_register_duplicate_email(mock_get_conn, user_data):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {"id": 1}
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    with pytest.raises(ValueError, match="Email already registered"):
        await AuthManager.register(user_data)

@pytest.mark.asyncio
@patch("modules.auth.manager.db.get_connection")
@patch("modules.auth.manager.verify_password", return_value=True)
@patch("modules.auth.manager.create_access_token", return_value="token123")
async def test_login_success(mock_token, mock_verify, mock_get_conn, user_data):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {"id": 1, "email": user_data.email, "password_hash": "hashedpass"}
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    token = await AuthManager.login(user_data.email, user_data.password)
    assert token == "token123"

@pytest.mark.asyncio
@patch("modules.auth.manager.db.get_connection")
async def test_login_no_user(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = None
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    with pytest.raises(ValueError, match="Invalid email or password"):
        await AuthManager.login("nouser@example.com", "password")

@pytest.mark.asyncio
@patch("modules.auth.manager.db.get_connection")
@patch("modules.auth.manager.verify_password", return_value=False)
async def test_login_wrong_password(mock_verify, mock_get_conn, user_data):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {"id": 1, "email": user_data.email, "password_hash": "hashedpass"}
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    with pytest.raises(ValueError, match="Invalid email or password"):
        await AuthManager.login(user_data.email, "wrongpassword") 