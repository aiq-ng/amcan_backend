# modules/chat/router.py
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from .models import MessageCreate, MessageResponse
from .manager import ChatManager
from modules.auth.utils import get_current_user, get_current_user_ws
from shared.response import success_response, error_response
from .utils import connect_websocket, disconnect_websocket, active_connections
from typing import List
from shared.db import db

router = APIRouter()

@router.post("/")
async def send_message(message: MessageCreate, current_user: dict = Depends(get_current_user)):
    try:
        message_data = await ChatManager.send_message(message, current_user["id"])  # Receiver determined in manager
        return success_response(data=message_data, message="Message sent successfully")
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/{appointment_id}")
async def get_chat_history(appointment_id: int, current_user: dict = Depends(get_current_user)):
    try:
        chat_history = await ChatManager.get_chat_history(appointment_id, current_user["id"])
        return success_response(data=chat_history, message="Chat history retrieved successfully")
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        return error_response(str(e), status_code=500)


@router.websocket("/{appointment_id}")
async def websocket_endpoint(appointment_id: int, websocket: WebSocket):
    print('websocket first layer')
    # Manually authenticate user for WebSocket
    current_user = await get_current_user_ws(websocket)
    print("current user data", current_user)
    try:
        user_id = current_user["id"]
        user_role = await connect_websocket(websocket, appointment_id, user_id)

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                message_create = MessageCreate(**data)
                
                # Save message to database
                receiver_id = await get_receiver_id(appointment_id, user_id)
                message_data = await ChatManager.save_message(
                    message_create.appointment_id,
                    user_id,
                    receiver_id,
                    message_create.message
                )
                
                # Broadcast to all connected users in this appointment
                await ChatManager.broadcast_message(appointment_id, {
                    "type": "message",
                    "data": message_data
                })

        except WebSocketDisconnect:
            await disconnect_websocket(appointment_id, user_id)
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})
            await disconnect_websocket(appointment_id, user_id)
    except HTTPException as e:
        await websocket.close(code=e.status_code)
        raise e

async def get_receiver_id(appointment_id: int, sender_id: int) -> int:
    """Determine the receiver_id based on the appointment."""
    async with db.get_connection() as conn:
        appointment = await conn.fetchrow(
            "SELECT user_id, doctor_id FROM appointments WHERE id = $1",
            appointment_id
        )
        if not appointment:
            raise ValueError("Appointment not found")
        receiver_id = appointment["doctor_id"] if sender_id == appointment["user_id"] else appointment["user_id"]

        if receiver_id == appointment["doctor_id"]:
            receiver_id = await conn.fetchval(
                "SELECT user_id FROM doctors WHERE id = $1",
                appointment["doctor_id"]
            )
        return receiver_id