import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from .models import CallInitiate, CallResponse
from .manager import VideoCallManager
from .utils import connect_websocket, disconnect_websocket, active_calls # active_calls might not be directly used here, but kept for context
from modules.auth.utils import get_current_user
from shared.response import success_response, error_response
from typing import List
from shared.db import db


router = APIRouter()
logger = logging.getLogger("video_call.router")

@router.websocket("/{appointment_id}")
async def video_call_endpoint(appointment_id: int, websocket: WebSocket):
    logger.info(f"WebSocket connection requested for appointment_id={appointment_id}")

    # REMOVED: await websocket.accept() - This is now handled by connect_websocket

    try:
        # It's crucial to receive initial data *after* the connection is accepted.
        # If connect_websocket handles accept(), then initial_data should be received after connect_websocket call.
        # However, your current flow sends token *before* connect_websocket.
        # Let's adjust the flow slightly to ensure accept() happens before any receive_json.
        # The token reception should occur after accept.
        # For simplicity and to match your original intent, I'll move the initial_data reception
        # to after the connect_websocket call, assuming connect_websocket will handle the accept().

        # First, accept the connection to allow initial data exchange
        await websocket.accept() # Keep this one, as initial_data is received immediately after.

        initial_data = await websocket.receive_json()
        logger.debug(f"Initial data received: {initial_data}")
        token = initial_data.get("token")
        if not token:
            logger.warning("No token provided, closing connection")
            await websocket.close(code=1008, reason="Authentication required")
            return

        try:
            logger.debug(f"Token received: {token}")
            current_user = await get_current_user(token)
            logger.debug(f"get_current_user returned: {current_user}")
            if not current_user or "id" not in current_user:
                logger.error(f"Invalid user or missing 'id' in current_user: {current_user}")
                await websocket.close(code=1008, reason="Invalid authentication")
                return
            user_id = current_user["id"]
            logger.info(f"Authenticated user_id={user_id} for appointment_id={appointment_id}")

            async with db.get_connection() as conn:
                appointment_data = await conn.fetchrow(
                    "SELECT patient_id, doctor_id FROM appointments WHERE id = $1",
                    appointment_id
                )

                # Pass the already accepted websocket to connect_websocket
                # connect_websocket will now *not* call accept() again.
                patient_id, doctor_id = await connect_websocket(websocket, appointment_id, user_id)
                logger.debug(f"Connected websocket for user_id={user_id}, patient_id={appointment_data.patient_id}, doctor_id={appointment_data.doctor_id}")

                receiver_id = doctor_id if user_id == patient_id else patient_id

                # this fetches the doctors reciever id
                if receiver_id == doctor_id:
                    receiver_id = await conn.fetchval(
                        "SELECT user_id FROM doctors WHERE id = $1",
                        doctor_id
                    )

                if user_id == patient_id:
                    logger.info(f"Patient (user_id={user_id}) initiates call to doctor_id={receiver_id}")
                    call_data = await VideoCallManager.initiate_call(appointment_id, user_id, receiver_id)
                    await VideoCallManager.broadcast_signal(appointment_id, {
                        "type": "call-initiated",
                        "data": call_data
                    })
                else:
                    logger.info(f"Doctor (user_id={user_id}) accepts call for appointment_id={appointment_id}")
                    await VideoCallManager.update_call_status(appointment_id, 'active')
                    await VideoCallManager.broadcast_signal(appointment_id, {
                        "type": "call-active",
                        "data": {"appointment_id": appointment_id, "status": "active"}
                    })

                try:
                    while True:
                        data = await websocket.receive_json()
                        logger.debug(f"Received data from user_id={user_id}: {data}")
                        if data.get("type") == "signal":
                            logger.info(f"Signal received for appointment_id={appointment_id}: {data['data']}")
                            await VideoCallManager.broadcast_signal(appointment_id, {
                                "type": "signal",
                                "data": data["data"]
                            })
                        elif data.get("type") == "end-call":
                            logger.info(f"End call requested by user_id={user_id} for appointment_id={appointment_id}")
                            await disconnect_websocket(appointment_id, user_id)
                            await VideoCallManager.update_call_status(appointment_id, 'ended')
                            await VideoCallManager.broadcast_signal(appointment_id, {
                                "type": "call-ended",
                                "data": {"appointment_id": appointment_id}
                            })
                            break

                except WebSocketDisconnect:
                    logger.warning(f"WebSocket disconnected for user_id={user_id}, appointment_id={appointment_id}")
                    await disconnect_websocket(appointment_id, user_id)
                except Exception as e:
                    logger.error(f"Exception in WebSocket loop: {e}", exc_info=True)
                    await websocket.send_json({"type": "error", "message": str(e)})
                    await disconnect_websocket(appointment_id, user_id)

        except ValueError as e:
            logger.error(f"Authentication error: {e}")
            await websocket.close(code=1008, reason=str(e))
    except Exception as e:
        logger.error(f"Error during WebSocket setup: {e}", exc_info=True)
        await websocket.close(code=1011, reason="Internal server error")