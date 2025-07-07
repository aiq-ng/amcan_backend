import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from modules.doctors.manager import DoctorManager
from modules.doctors.models import DoctorCreate, Availability
from datetime import datetime
import json

@pytest_asyncio.fixture
def doctor_data():
    return DoctorCreate(
        user_id=1,
        title="Psychiatrist",
        bio="Experienced doctor",
        experience_years=10,
        patients_count=100,
        location="Lagos",
        availability=[Availability(day="Mon", slots=["9:00AM", "10:00AM"])]
    )

@pytest.mark.asyncio
@patch("modules.doctors.manager.db.get_connection")
async def test_create_doctor_success(mock_get_conn, doctor_data):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {
        "id": 1,
        "title": doctor_data.title,
        "bio": doctor_data.bio,
        "experience_years": doctor_data.experience_years,
        "patients_count": doctor_data.patients_count,
        "location": doctor_data.location,
        "created_at": datetime.now(),
        "user_id": doctor_data.user_id,
        "availability": json.dumps([{"day": "Mon", "slots": ["9:00AM", "10:00AM"]}])
    }
    mock_conn.execute.return_value = None
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await DoctorManager.create_doctor(doctor_data, doctor_data.user_id)
    assert result["title"] == doctor_data.title
    assert result["user_id"] == doctor_data.user_id
    assert isinstance(result["availability"], list)

@pytest.mark.asyncio
@patch("modules.doctors.manager.db.get_connection")
async def test_get_doctors_success(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = [
        {"id": 1, "user_id": 1, "title": "Psychiatrist", "bio": "Experienced doctor", "experience_years": 10, "patients_count": 100, "location": "Lagos", "rating": 4.5, "availability": json.dumps([{"day": "Mon", "slots": ["9:00AM"]}]), "created_at": datetime.now(), "review_count": 2, "avg_rating": 4.5, "doctor_email": "doc@example.com", "doctor_first_name": "Jane", "doctor_last_name": "Doe"}
    ]
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await DoctorManager.get_doctors()
    assert isinstance(result, list)
    assert result[0]["title"] == "Psychiatrist"

@pytest.mark.asyncio
@patch("modules.doctors.manager.db.get_connection")
async def test_get_doctors_empty(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = []
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await DoctorManager.get_doctors()
    assert result == []

@pytest.mark.asyncio
@patch("modules.doctors.manager.db.get_connection")
async def test_get_doctor_success(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {
        "id": 1, "user_id": 1, "title": "Psychiatrist", "bio": "Experienced doctor", "experience_years": 10, "patients_count": 100, "location": "Lagos", "rating": 4.5, "availability": json.dumps([{"day": "Mon", "slots": ["9:00AM"]}]), "created_at": datetime.now(), "review_count": 2, "avg_rating": 4.5, "doctor_email": "doc@example.com", "doctor_first_name": "Jane", "doctor_last_name": "Doe"
    }
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await DoctorManager.get_doctor(1)
    assert result["id"] == 1
    assert result["title"] == "Psychiatrist"

@pytest.mark.asyncio
@patch("modules.doctors.manager.db.get_connection")
async def test_get_doctor_not_found(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = None
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await DoctorManager.get_doctor(1)
    assert result is None

@pytest.mark.asyncio
@patch("modules.doctors.manager.db.get_connection")
async def test_add_review_success(mock_get_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {
        "id": 1, "doctor_id": 1, "user_id": 2, "rating": 5, "comment": "Great doctor!", "created_at": datetime.now()
    }
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    result = await DoctorManager.add_review(1, 2, 5, "Great doctor!")
    assert result["doctor_id"] == 1
    assert result["user_id"] == 2
    assert result["rating"] == 5
    assert result["comment"] == "Great doctor!"
