import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from modules.appointments.manager import AppointmentManager
from modules.appointments.models import AppointmentCreate
from datetime import datetime

@pytest_asyncio.fixture
def appointment_data():
    # Monday at 9:00AM
    return AppointmentCreate(doctor_id=2, slot_time=datetime.strptime("2024-06-10T09:00:00", "%Y-%m-%dT%H:%M:%S"))

@pytest.mark.asyncio
@patch("modules.appointments.manager.db.get_connection")
async def test_book_appointment_success(mock_get_conn, appointment_data):
    mock_conn = AsyncMock()
    # Doctor available, slot available, not booked
    mock_conn.fetchrow.side_effect = [
        {"availability": '[{"day": "Mon", "slots": ["9:00AM"]}]'},  # doctor
        None,  # existing
        {"id": 1, "doctor_id": 2, "user_id": 1, "slot_time": appointment_data.slot_time, "status": "pending", "created_at": datetime.now()}  # insert
    ]
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await AppointmentManager.book_appointment(appointment_data, 1)
    assert result["doctor_id"] == 2
    assert result["user_id"] == 1
    assert result["status"] == "pending"

@pytest.mark.asyncio
@patch("modules.appointments.manager.db.get_connection")
async def test_book_appointment_doctor_not_found(mock_get_conn, appointment_data):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = None  # doctor not found
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    with pytest.raises(ValueError, match="Doctor not found"):
        await AppointmentManager.book_appointment(appointment_data, 1)

@pytest.mark.asyncio
@patch("modules.appointments.manager.db.get_connection")
async def test_book_appointment_slot_not_available(mock_get_conn, appointment_data):
    mock_conn = AsyncMock()
    # Doctor found, but slot not available
    mock_conn.fetchrow.side_effect = [
        {"availability": '[{"day": "Tue", "slots": ["10:00AM"]}]'},  # doctor
    ]
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    with pytest.raises(ValueError, match="Slot not available"):
        await AppointmentManager.book_appointment(appointment_data, 1)

@pytest.mark.asyncio
@patch("modules.appointments.manager.db.get_connection")
async def test_book_appointment_slot_already_booked(mock_get_conn, appointment_data):
    mock_conn = AsyncMock()
    # Doctor found, slot available, but already booked
    mock_conn.fetchrow.side_effect = [
        {"availability": '[{"day": "Mon", "slots": ["9:00AM"]}]'},  # doctor
        1  # existing slot booked
    ]
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    with pytest.raises(ValueError, match="Slot already booked"):
        await AppointmentManager.book_appointment(appointment_data, 1)

@pytest.mark.asyncio
@patch("modules.appointments.manager.db.get_connection")
async def test_get_appointments_success(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = [
        {"id": 1, "doctor_id": 2, "user_id": 1, "slot_time": datetime.now(), "status": "pending", "created_at": datetime.now()}
    ]
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await AppointmentManager.get_appointments(1)
    assert isinstance(result, list)
    assert result[0]["doctor_id"] == 2

@pytest.mark.asyncio
@patch("modules.appointments.manager.db.get_connection")
async def test_get_appointments_empty(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = []
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await AppointmentManager.get_appointments(1)
    assert result == []

@pytest.mark.asyncio
@patch("modules.appointments.manager.db.get_connection")
async def test_confirm_appointment_success(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {"id": 1, "doctor_id": 2, "user_id": 1, "slot_time": datetime.now(), "status": "confirmed", "created_at": datetime.now()}
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await AppointmentManager.confirm_appointment(1, 1)
    assert result["status"] == "confirmed"

@pytest.mark.asyncio
@patch("modules.appointments.manager.db.get_connection")
async def test_confirm_appointment_not_found(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = None
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    with pytest.raises(ValueError, match="Appointment not found or cannot be confirmed"):
        await AppointmentManager.confirm_appointment(1, 1)

@pytest.mark.asyncio
@patch("modules.appointments.manager.db.get_connection")
async def test_cancel_appointment_success(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {"id": 1, "doctor_id": 2, "user_id": 1, "slot_time": datetime.now(), "status": "cancelled", "created_at": datetime.now()}
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await AppointmentManager.cancel_appointment(1, 1)
    assert result["status"] == "cancelled"

@pytest.mark.asyncio
@patch("modules.appointments.manager.db.get_connection")
async def test_cancel_appointment_not_found(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = None
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    with pytest.raises(ValueError, match="Appointment not found or cannot be cancelled"):
        await AppointmentManager.cancel_appointment(1, 1) 