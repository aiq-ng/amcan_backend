import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from modules.chat.manager import ChatManager
from modules.chat.models import MessageCreate
from datetime import datetime

@pytest_asyncio.fixture
def message_data():
    return MessageCreate(appointment_id=1, message="Hello!")

@pytest.mark.asyncio
@patch("modules.chat.manager.db.get_connection")
async def test_send_message_success(mock_get_conn, message_data):
    mock_conn = AsyncMock()
    # fetchrow: appointment check, then insert message row
    mock_conn.fetchrow.side_effect = [
        {"id": 1, "status": "confirmed"},  # appointment
        {"id": 1, "appointment_id": 1, "sender_id": 2, "receiver_id": 3, "message": message_data.message, "sent_at": datetime.now()}
    ]
    # fetchval: doctor_id, receiver_id, receiver_id from doctors
    mock_conn.fetchval.side_effect = [2, 3, 3]
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await ChatManager.send_message(message_data, sender_id=2)
    assert result["message"] == message_data.message
    assert result["appointment_id"] == 1

@pytest.mark.asyncio
@patch("modules.chat.manager.db.get_connection")
async def test_send_message_no_confirmed_appointment(mock_get_conn, message_data):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = None  # appointment not found
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    with pytest.raises(ValueError, match="No confirmed appointment found"):
        await ChatManager.send_message(message_data, sender_id=2)

@pytest.mark.asyncio
@patch("modules.chat.manager.db.get_connection")
async def test_get_chat_history_success(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {"id": 1, "status": "confirmed"}
    mock_conn.fetch.return_value = [
        {"id": 1, "appointment_id": 1, "sender_id": 2, "receiver_id": 3, "message": "Hello!", "sent_at": datetime.now()}
    ]
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await ChatManager.get_chat_history(1, 2)
    assert isinstance(result, list)
    assert result[0]["message"] == "Hello!"

@pytest.mark.asyncio
@patch("modules.chat.manager.db.get_connection")
async def test_get_chat_history_no_confirmed_appointment(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = None  # appointment not found
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    with pytest.raises(ValueError, match="No confirmed appointment found"):
        await ChatManager.get_chat_history(1, 2)

@pytest.mark.asyncio
@patch("modules.chat.manager.db.get_connection")
async def test_save_message_success(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {
        "id": 1, "appointment_id": 1, "sender_id": 2, "receiver_id": 3, "message": "Hello!", "sent_at": datetime.now()
    }
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await ChatManager.save_message(1, 2, 3, "Hello!")
    assert result["message"] == "Hello!"
    assert result["appointment_id"] == 1 