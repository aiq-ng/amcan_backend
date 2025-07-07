import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from modules.video_call.manager import VideoCallManager
from datetime import datetime

@pytest.mark.asyncio
@patch("modules.video_call.manager.db.get_connection")
async def test_initiate_call_success(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {
        "id": 1,
        "appointment_id": 1,
        "initiator_id": 2,
        "receiver_id": 3,
        "start_time": datetime.now(),
        "end_time": None,
        "status": "initiated",
        "created_at": datetime.now()
    }
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await VideoCallManager.initiate_call(1, 2, 3)
    assert result["appointment_id"] == 1
    assert result["initiator_id"] == 2
    assert result["receiver_id"] == 3
    assert result["status"] == "initiated"

@pytest.mark.asyncio
@patch("modules.video_call.manager.db.get_connection")
async def test_update_call_status_success(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.execute.return_value = "UPDATE 1"
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    await VideoCallManager.update_call_status(1, "ended")
    mock_conn.execute.assert_called_once()

@pytest.mark.asyncio
@patch("modules.video_call.manager.active_calls", new_callable=dict)
async def test_broadcast_signal_no_active_calls(mock_active_calls):
    # No active calls for appointment_id
    mock_active_calls.clear()
    await VideoCallManager.broadcast_signal(1, {"type": "offer", "sdp": "test"})
    # Should not raise

@pytest.mark.asyncio
@patch("modules.video_call.manager.active_calls", new_callable=dict)
async def test_broadcast_signal_with_active_calls(mock_active_calls):
    # Simulate an active call with a mock websocket
    class MockWebSocket:
        async def send_json(self, data):
            self.sent = data
    ws = MockWebSocket()
    mock_active_calls[1] = {2: ws}
    await VideoCallManager.broadcast_signal(1, {"type": "offer", "sdp": "test"})
    assert hasattr(ws, "sent")
    assert ws.sent == {"type": "offer", "sdp": "test"} 