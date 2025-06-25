# modules/chat/router.py
from fastapi import APIRouter, Depends, HTTPException
from .models import MessageCreate, MessageResponse
from .manager import ChatManager
from modules.auth.utils import get_current_user
from shared.response import success_response, error_response
from typing import List

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