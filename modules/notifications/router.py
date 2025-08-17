from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import List, Optional
import json
from .models import NotificationCreate, NotificationUpdate, NotificationResponse, NotificationPreferences, NotificationStatus
from .manager import NotificationManager
from .utils import manager
from modules.auth.utils import get_current_user, get_current_admin, get_current_user_ws
from shared.response import success_response, error_response

router = APIRouter()

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new notification (Admin only)"""
    try:
        notification = await NotificationManager.create_notification(notification_data)
        return success_response(data=notification, message="Notification created successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/")
async def get_my_notifications(
    status: Optional[NotificationStatus] = Query(None, description="Filter by notification status"),
    limit: int = Query(50, ge=1, le=100, description="Number of notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's notifications with optional filtering"""
    try:
        notifications = await NotificationManager.get_user_notifications(
            current_user["id"], 
            status=status, 
            limit=limit, 
            offset=offset
        )
        return success_response(data=notifications, message="Notifications retrieved successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread notifications for current user"""
    try:
        count = await NotificationManager.get_unread_count(current_user["id"])
        return success_response(data={"unread_count": count}, message="Unread count retrieved successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read"""
    try:
        success = await NotificationManager.mark_notification_read(notification_id, current_user["id"])
        if not success:
            return error_response("Notification not found or already read", status_code=404)
        return success_response(data=None, message="Notification marked as read")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.put("/mark-all-read")
async def mark_all_notifications_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read for current user"""
    try:
        await NotificationManager.mark_all_notifications_read(current_user["id"])
        return success_response(data=None, message="All notifications marked as read")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a notification"""
    try:
        success = await NotificationManager.delete_notification(notification_id, current_user["id"])
        if not success:
            return error_response("Notification not found", status_code=404)
        return success_response(data=None, message="Notification deleted successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.post("/bulk")
async def send_bulk_notification(
    user_ids: List[int],
    title: str,
    message: str,
    notification_type: str = "system",
    priority: str = "medium",
    current_admin: dict = Depends(get_current_admin)
):
    """Send notification to multiple users (Admin only)"""
    try:
        count = await NotificationManager.send_bulk_notification(
            user_ids, title, message, notification_type, priority
        )
        return success_response(data={"sent_count": count}, message=f"Notification sent to {count} users")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/preferences")
async def get_notification_preferences(current_user: dict = Depends(get_current_user)):
    """Get notification preferences for current user"""
    try:
        preferences = await NotificationManager.get_notification_preferences(current_user["id"])
        if not preferences:
            return success_response(data=None, message="No preferences found")
        return success_response(data=preferences, message="Notification preferences retrieved successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.put("/preferences")
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: dict = Depends(get_current_user)
):
    """Update notification preferences for current user"""
    try:
        # This would need to be implemented in the manager
        # For now, returning a placeholder
        return success_response(data=preferences.dict(), message="Notification preferences updated successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/admin/all")
async def get_all_notifications_admin(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    status: Optional[str] = Query(None, description="Filter by notification status"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    priority: Optional[str] = Query(None, description="Filter by priority level"),
    user_search: Optional[str] = Query(None, description="Search by user email, first name, last name, or full name (partial match)"),
    created_at_from: Optional[str] = Query(None, description="Filter by creation date from (YYYY-MM-DD)"),
    created_at_to: Optional[str] = Query(None, description="Filter by creation date to (YYYY-MM-DD)"),
    scheduled_at_from: Optional[str] = Query(None, description="Filter by scheduled date from (YYYY-MM-DD)"),
    scheduled_at_to: Optional[str] = Query(None, description="Filter by scheduled date to (YYYY-MM-DD)"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get all notifications with pagination and filters (Admin only)
    
    Available filters:
    - status: unread, read, archived
    - notification_type: appointment, subscription, system, reminder, alert, message
    - priority: low, medium, high, urgent
    - user_search: search by email, first name, last name, or full name (partial match)
    - created_at_from/created_at_to: date range for creation date
    - scheduled_at_from/scheduled_at_to: date range for scheduled date
    
    Available sort fields:
    - id, user_id, notification_type, status, priority, created_at, scheduled_at, read_at
    
    Sort order: asc or desc
    """
    try:
        # Parse date strings to datetime objects
        created_at_from_dt = None
        created_at_to_dt = None
        scheduled_at_from_dt = None
        scheduled_at_to_dt = None
        
        if created_at_from:
            try:
                # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS formats
                if 'T' in created_at_from:
                    created_at_from_dt = datetime.fromisoformat(created_at_from)
                else:
                    created_at_from_dt = datetime.strptime(created_at_from, "%Y-%m-%d")
            except ValueError:
                return error_response("Invalid created_at_from format. Use YYYY-MM-DD", status_code=400)
        
        if created_at_to:
            try:
                # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS formats
                if 'T' in created_at_to:
                    created_at_to_dt = datetime.fromisoformat(created_at_to)
                else:
                    created_at_to_dt = datetime.strptime(created_at_to, "%Y-%m-%d")
            except ValueError:
                return error_response("Invalid created_at_to format. Use YYYY-MM-DD", status_code=400)
        
        if scheduled_at_from:
            try:
                # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS formats
                if 'T' in scheduled_at_from:
                    scheduled_at_from_dt = datetime.fromisoformat(scheduled_at_from)
                else:
                    scheduled_at_from_dt = datetime.strptime(scheduled_at_from, "%Y-%m-%d")
            except ValueError:
                return error_response("Invalid scheduled_at_from format. Use YYYY-MM-DD", status_code=400)
        
        if scheduled_at_to:
            try:
                # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS formats
                if 'T' in scheduled_at_to:
                    scheduled_at_to_dt = datetime.fromisoformat(scheduled_at_to)
                else:
                    scheduled_at_to_dt = datetime.strptime(scheduled_at_to, "%Y-%m-%d")
            except ValueError:
                return error_response("Invalid scheduled_at_to format. Use YYYY-MM-DD", status_code=400)
        
        result = await NotificationManager.get_all_notifications(
            page=page,
            page_size=page_size,
            status=status,
            notification_type=notification_type,
            priority=priority,
            user_search=user_search,
            created_at_from=created_at_from_dt,
            created_at_to=created_at_to_dt,
            scheduled_at_from=scheduled_at_from_dt,
            scheduled_at_to=scheduled_at_to_dt,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return success_response(
            data=result, 
            message=f"Retrieved {len(result['notifications'])} notifications (page {page} of {result['total_pages']})"
        )
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications"""
    try:
        # Get user from token in query params
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Missing token")
            return
        
        # Validate user
        try:
            user = await get_current_user_ws(websocket)
            user_id = user["id"]
        except Exception as e:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Connect to WebSocket
        await manager.connect(websocket, user_id)
        
        try:
            while True:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "subscribe":
                    notification_type = message.get("notification_type")
                    if notification_type:
                        manager.subscribe_user(user_id, notification_type)
                        await websocket.send_text(json.dumps({
                            "type": "subscribed",
                            "notification_type": notification_type
                        }))
                
                elif message.get("type") == "unsubscribe":
                    notification_type = message.get("notification_type")
                    if notification_type:
                        manager.unsubscribe_user(user_id, notification_type)
                        await websocket.send_text(json.dumps({
                            "type": "unsubscribed",
                            "notification_type": notification_type
                        }))
                
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
        except WebSocketDisconnect:
            manager.disconnect(user_id)
        except Exception as e:
            print(f"WebSocket error: {e}")
            manager.disconnect(user_id)
            
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        await websocket.close(code=4000, reason="Connection error")
