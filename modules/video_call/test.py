from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
from shared.db import db
import pytest

class DummyWebSocket:
    def __init__(self):
        self.closed = False
        self.close_code = None
        self.close_reason = None

    async def close(self, code=None, reason=None):
        self.closed = True
        self.close_code = code
        self.close_reason = reason

@pytest.mark.asyncio
async def test_connect_websocket_success(monkeypatch):
    class DummyConn:
        async def fetchrow(self, query, appointment_id):
            return {"patient_id": 1, "doctor_id": 2, "status": "confirmed"}
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass

    monkeypatch.setattr(db, "get_connection", lambda: DummyConn())

    ws = DummyWebSocket()
    appointment_id = 123
    user_id = 1  # patient
    active_calls.clear()
    patient_id, doctor_id = await connect_websocket(ws, appointment_id, user_id)
    assert patient_id == 1
    assert doctor_id == 2
    assert appointment_id in active_calls
    assert user_id in active_calls[appointment_id]
    assert active_calls[appointment_id][user_id] is ws

@pytest.mark.asyncio
async def test_connect_websocket_unauthorized(monkeypatch):
    class DummyConn:
        async def fetchrow(self, query, appointment_id):
            return {"patient_id": 1, "doctor_id": 2, "status": "confirmed"}
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass

    monkeypatch.setattr(db, "get_connection", lambda: DummyConn())

    ws = DummyWebSocket()
    appointment_id = 123
    user_id = 99  # not patient or doctor
    active_calls.clear()
    with pytest.raises(ValueError):
        await connect_websocket(ws, appointment_id, user_id)
    assert ws.closed
    assert ws.close_code == 1008

@pytest.mark.asyncio
async def test_connect_websocket_no_appointment(monkeypatch):
    class DummyConn:
        async def fetchrow(self, query, appointment_id):
            return None
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass

    monkeypatch.setattr(db, "get_connection", lambda: DummyConn())

    ws = DummyWebSocket()
    appointment_id = 123
    user_id = 1
    active_calls.clear()
    with pytest.raises(ValueError):
        await connect_websocket(ws, appointment_id, user_id)
    assert ws.closed
    assert ws.close_code == 1008

@pytest.mark.asyncio
async def test_disconnect_websocket_removes_user_and_ends_call(monkeypatch):
    class DummyConn:
        def __init__(self):
            self.executed = False
        async def execute(self, query, appointment_id):
            self.executed = True
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass

    dummy_conn = DummyConn()
    monkeypatch.setattr(db, "get_connection", lambda: dummy_conn)

    appointment_id = 123
    user_id = 1
    active_calls.clear()
    active_calls[appointment_id] = {user_id: DummyWebSocket()}
    await disconnect_websocket(appointment_id, user_id)
    assert appointment_id not in active_calls
    assert dummy_conn.executed

@pytest.mark.asyncio
async def test_disconnect_websocket_removes_only_user(monkeypatch):
    class DummyConn:
        def __init__(self):
            self.executed = False
        async def execute(self, query, appointment_id):
            self.executed = True
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass

    dummy_conn = DummyConn()
    monkeypatch.setattr(db, "get_connection", lambda: dummy_conn)

    appointment_id = 123
    user_id1 = 1
    user_id2 = 2
    active_calls.clear()
    active_calls[appointment_id] = {user_id1: DummyWebSocket(), user_id2: DummyWebSocket()}
    await disconnect_websocket(appointment_id, user_id1)
    assert appointment_id in active_calls
    assert user_id1 not in active_calls[appointment_id]
    assert user_id2 in active_calls[appointment_id]
    assert not dummy_conn.executed