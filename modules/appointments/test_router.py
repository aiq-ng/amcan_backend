import pytest
from httpx import AsyncClient
from modules.appointments.manager import AppointmentManager
from modules.auth.utils import get_current_user
from main import app
from datetime import datetime

@pytest.fixture
def fake_user():
    return {"id": 1, "email": "test@example.com"}

@pytest.mark.asyncio
async def test_book_appointment_success(monkeypatch, fake_user):
    async def mock_book_appointment(appointment, user_id):
        return {"id": 1, "doctor_id": 2, "user_id": user_id, "slot_time": datetime.now().isoformat(), "status": "pending", "created_at": datetime.now().isoformat()}
    app.dependency_overrides[get_current_user] = lambda: fake_user
    monkeypatch.setattr(AppointmentManager, "book_appointment", mock_book_appointment)
    payload = {"doctor_id": 2, "slot_time": datetime.now().isoformat()}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/appointments/", json=payload)
    assert resp.status_code == 200
    assert resp.json()["data"]["doctor_id"] == 2
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_book_appointment_slot_unavailable(monkeypatch, fake_user):
    async def mock_book_appointment(appointment, user_id):
        raise ValueError("Slot not available")
    app.dependency_overrides[get_current_user] = lambda: fake_user
    monkeypatch.setattr(AppointmentManager, "book_appointment", mock_book_appointment)
    payload = {"doctor_id": 2, "slot_time": datetime.now().isoformat()}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/appointments/", json=payload)
    assert resp.status_code == 400
    assert resp.json()["error"] == "Slot not available"
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_get_appointments_success(monkeypatch, fake_user):
    async def mock_get_appointments(user_id):
        return [{"id": 1, "doctor_id": 2, "user_id": user_id, "slot_time": datetime.now().isoformat(), "status": "pending", "created_at": datetime.now().isoformat()}]
    app.dependency_overrides[get_current_user] = lambda: fake_user
    monkeypatch.setattr(AppointmentManager, "get_appointments", mock_get_appointments)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/appointments/")
    assert resp.status_code == 200
    assert isinstance(resp.json()["data"], list)
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_confirm_appointment_success(monkeypatch, fake_user):
    async def mock_confirm_appointment(appointment_id, user_id):
        return {"id": appointment_id, "doctor_id": 2, "user_id": user_id, "slot_time": datetime.now().isoformat(), "status": "confirmed", "created_at": datetime.now().isoformat()}
    app.dependency_overrides[get_current_user] = lambda: fake_user
    monkeypatch.setattr(AppointmentManager, "confirm_appointment", mock_confirm_appointment)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/appointments/1/confirm")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "confirmed"
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_confirm_appointment_not_found(monkeypatch, fake_user):
    async def mock_confirm_appointment(appointment_id, user_id):
        raise ValueError("Appointment not found or cannot be confirmed")
    app.dependency_overrides[get_current_user] = lambda: fake_user
    monkeypatch.setattr(AppointmentManager, "confirm_appointment", mock_confirm_appointment)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/appointments/1/confirm")
    assert resp.status_code == 400
    assert resp.json()["error"] == "Appointment not found or cannot be confirmed"
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_cancel_appointment_success(monkeypatch, fake_user):
    async def mock_cancel_appointment(appointment_id, user_id):
        return {"id": appointment_id, "doctor_id": 2, "user_id": user_id, "slot_time": datetime.now().isoformat(), "status": "cancelled", "created_at": datetime.now().isoformat()}
    app.dependency_overrides[get_current_user] = lambda: fake_user
    monkeypatch.setattr(AppointmentManager, "cancel_appointment", mock_cancel_appointment)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/appointments/1/cancel")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "cancelled"
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_cancel_appointment_not_found(monkeypatch, fake_user):
    async def mock_cancel_appointment(appointment_id, user_id):
        raise ValueError("Appointment not found or cannot be cancelled")
    app.dependency_overrides[get_current_user] = lambda: fake_user
    monkeypatch.setattr(AppointmentManager, "cancel_appointment", mock_cancel_appointment)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/appointments/1/cancel")
    assert resp.status_code == 400
    assert resp.json()["error"] == "Appointment not found or cannot be cancelled"
    app.dependency_overrides = {} 