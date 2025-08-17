import logging
from datetime import datetime
from typing import List, Optional
from .models import NotificationCreate, NotificationUpdate, NotificationResponse, NotificationStatus, NotificationType
from shared.db import db

logger = logging.getLogger(__name__)

class NotificationManager:
    @staticmethod
    async def create_notification(notification_data: NotificationCreate) -> dict:
        """Create a new notification"""
        logger.info(f"[NOTIFICATION MANAGER] Creating notification for user: {notification_data.user_id}")
        
        async with db.get_connection() as conn:
            result = await conn.fetchrow(
                """
                INSERT INTO notifications (user_id, title, message, notification_type, status, priority, data, scheduled_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, user_id, title, message, notification_type, status, priority, data, created_at, read_at, scheduled_at
                """,
                notification_data.user_id,
                notification_data.title,
                notification_data.message,
                notification_data.notification_type,
                NotificationStatus.UNREAD,
                notification_data.priority,
                notification_data.data,
                notification_data.scheduled_at
            )
            
            logger.info(f"[NOTIFICATION MANAGER] Notification created successfully: {result['id']}")
            return dict(result)

    @staticmethod
    async def get_user_notifications(
        user_id: int, 
        status: Optional[NotificationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """Get notifications for a user with optional filtering"""
        logger.info(f"[NOTIFICATION MANAGER] Getting notifications for user: {user_id}")
        
        async with db.get_connection() as conn:
            query = """
                SELECT id, user_id, title, message, notification_type, status, priority, data, created_at, read_at, scheduled_at
                FROM notifications
                WHERE user_id = $1
            """
            params = [user_id]
            
            if status:
                query += " AND status = $2"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT $%d OFFSET $%d" % (len(params) + 1, len(params) + 2)
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            notifications = [dict(row) for row in rows]
            
            logger.info(f"[NOTIFICATION MANAGER] Retrieved {len(notifications)} notifications for user: {user_id}")
            return notifications

    @staticmethod
    async def mark_notification_read(notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        logger.info(f"[NOTIFICATION MANAGER] Marking notification as read: {notification_id}")
        
        async with db.get_connection() as conn:
            result = await conn.execute(
                """
                UPDATE notifications 
                SET status = 'read', read_at = $1
                WHERE id = $2 AND user_id = $3
                """,
                datetime.utcnow(),
                notification_id,
                user_id
            )
            
            if result == "UPDATE 1":
                logger.info(f"[NOTIFICATION MANAGER] Notification marked as read: {notification_id}")
                return True
            else:
                logger.warning(f"[NOTIFICATION MANAGER] Failed to mark notification as read: {notification_id}")
                return False

    @staticmethod
    async def mark_all_notifications_read(user_id: int) -> bool:
        """Mark all notifications as read for a user"""
        logger.info(f"[NOTIFICATION MANAGER] Marking all notifications as read for user: {user_id}")
        
        async with db.get_connection() as conn:
            result = await conn.execute(
                """
                UPDATE notifications 
                SET status = 'read', read_at = $1
                WHERE user_id = $2 AND status = 'unread'
                """,
                datetime.utcnow(),
                user_id
            )
            
            logger.info(f"[NOTIFICATION MANAGER] All notifications marked as read for user: {user_id}")
            return True

    @staticmethod
    async def delete_notification(notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        logger.info(f"[NOTIFICATION MANAGER] Deleting notification: {notification_id}")
        
        async with db.get_connection() as conn:
            result = await conn.execute(
                """
                DELETE FROM notifications 
                WHERE id = $1 AND user_id = $2
                """,
                notification_id,
                user_id
            )
            
            if result == "DELETE 1":
                logger.info(f"[NOTIFICATION MANAGER] Notification deleted: {notification_id}")
                return True
            else:
                logger.warning(f"[NOTIFICATION MANAGER] Failed to delete notification: {notification_id}")
                return False

    @staticmethod
    async def get_unread_count(user_id: int) -> int:
        """Get count of unread notifications for a user"""
        logger.info(f"[NOTIFICATION MANAGER] Getting unread count for user: {user_id}")
        
        async with db.get_connection() as conn:
            count = await conn.fetchval(
                """
                SELECT COUNT(*) 
                FROM notifications 
                WHERE user_id = $1 AND status = 'unread'
                """,
                user_id
            )
            
            logger.info(f"[NOTIFICATION MANAGER] Unread count for user {user_id}: {count}")
            return count

    @staticmethod
    async def send_bulk_notification(
        user_ids: List[int], 
        title: str, 
        message: str, 
        notification_type: NotificationType,
        priority: str = "medium"
    ) -> int:
        """Send notification to multiple users"""
        logger.info(f"[NOTIFICATION MANAGER] Sending bulk notification to {len(user_ids)} users")
        
        async with db.get_connection() as conn:
            # Create notifications for all users
            values = []
            for i, user_id in enumerate(user_ids):
                values.append(f"(${i*7+1}, ${i*7+2}, ${i*7+3}, ${i*7+4}, ${i*7+5}, ${i*7+6}, ${i*7+7})")
            
            query = f"""
                INSERT INTO notifications (user_id, title, message, notification_type, status, priority, created_at)
                VALUES {', '.join(values)}
            """
            
            # Flatten the parameters
            params = []
            for user_id in user_ids:
                params.extend([user_id, title, message, notification_type, NotificationStatus.UNREAD, priority, datetime.utcnow()])
            
            result = await conn.execute(query, *params)
            
            logger.info(f"[NOTIFICATION MANAGER] Bulk notification sent successfully to {len(user_ids)} users")
            return len(user_ids)

    @staticmethod
    async def get_notification_preferences(user_id: int) -> Optional[dict]:
        """Get notification preferences for a user"""
        logger.info(f"[NOTIFICATION MANAGER] Getting notification preferences for user: {user_id}")
        
        async with db.get_connection() as conn:
            result = await conn.fetchrow(
                """
                SELECT user_id, email_notifications, push_notifications, sms_notifications, 
                       appointment_reminders, subscription_alerts, system_notifications
                FROM notification_preferences
                WHERE user_id = $1
                """,
                user_id
            )
            
            if result:
                logger.info(f"[NOTIFICATION MANAGER] Found preferences for user: {user_id}")
                return dict(result)
            else:
                logger.info(f"[NOTIFICATION MANAGER] No preferences found for user: {user_id}")
                return None

    @staticmethod
    async def get_all_notifications(
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        notification_type: Optional[str] = None,
        priority: Optional[str] = None,
        user_search: Optional[str] = None,
        created_at_from: Optional[datetime] = None,
        created_at_to: Optional[datetime] = None,
        scheduled_at_from: Optional[datetime] = None,
        scheduled_at_to: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> dict:
        """
        Get all notifications with pagination and filters (Admin only)
        Returns: {notifications: List[dict], total_count: int, total_pages: int, current_page: int}
        """
        logger.info(f"[NOTIFICATION MANAGER] Getting all notifications with filters - page: {page}, page_size: {page_size}")
        
        async with db.get_connection() as conn:
            # Build the base query with filters
            base_query = """
                SELECT 
                    n.id,
                    n.user_id,
                    n.title,
                    n.message,
                    n.notification_type,
                    n.status,
                    n.priority,
                    n.data,
                    n.read_at,
                    n.scheduled_at,
                    n.created_at,
                    u.email as user_email,
                    p.first_name,
                    p.last_name
                FROM notifications n
                JOIN users u ON n.user_id = u.id
                LEFT JOIN patients p ON p.user_id = u.id
                WHERE 1=1
            """
            
            # Build count query
            count_query = """
                SELECT COUNT(*) 
                FROM notifications n
                JOIN users u ON n.user_id = u.id
                LEFT JOIN patients p ON p.user_id = u.id
                WHERE 1=1
            """
            
            # Parameters for both queries
            params = []
            param_count = 0
            
            # Add filters
            if status:
                param_count += 1
                base_query += f" AND n.status = ${param_count}"
                count_query += f" AND n.status = ${param_count}"
                params.append(status)
            
            if notification_type:
                param_count += 1
                base_query += f" AND n.notification_type = ${param_count}"
                count_query += f" AND n.notification_type = ${param_count}"
                params.append(notification_type)
            
            if priority:
                param_count += 1
                base_query += f" AND n.priority = ${param_count}"
                count_query += f" AND n.priority = ${param_count}"
                params.append(priority)
            
            if user_search:
                param_count += 1
                base_query += f" AND (u.email ILIKE ${param_count} OR p.first_name ILIKE ${param_count} OR p.last_name ILIKE ${param_count} OR CONCAT(p.first_name, ' ', p.last_name) ILIKE ${param_count})"
                count_query += f" AND (u.email ILIKE ${param_count} OR p.first_name ILIKE ${param_count} OR p.last_name ILIKE ${param_count} OR CONCAT(p.first_name, ' ', p.last_name) ILIKE ${param_count})"
                params.append(f"%{user_search}%")
            
            if created_at_from:
                param_count += 1
                base_query += f" AND n.created_at >= ${param_count}"
                count_query += f" AND n.created_at >= ${param_count}"
                params.append(created_at_from)
            
            if created_at_to:
                param_count += 1
                base_query += f" AND n.created_at <= ${param_count}"
                count_query += f" AND n.created_at <= ${param_count}"
                params.append(created_at_to)
            
            if scheduled_at_from:
                param_count += 1
                base_query += f" AND n.scheduled_at >= ${param_count}"
                count_query += f" AND n.scheduled_at >= ${param_count}"
                params.append(scheduled_at_from)
            
            if scheduled_at_to:
                param_count += 1
                base_query += f" AND n.scheduled_at <= ${param_count}"
                count_query += f" AND n.scheduled_at <= ${param_count}"
                params.append(scheduled_at_to)
            
            # Validate sort parameters
            valid_sort_fields = ["id", "user_id", "notification_type", "status", "priority", "created_at", "scheduled_at", "read_at"]
            if sort_by not in valid_sort_fields:
                sort_by = "created_at"
            
            if sort_order.lower() not in ["asc", "desc"]:
                sort_order = "desc"
            
            # Add sorting
            base_query += f" ORDER BY n.{sort_by} {sort_order.upper()}"
            
            # Add pagination
            offset = (page - 1) * page_size
            param_count += 1
            base_query += f" LIMIT ${param_count}"
            params.append(page_size)
            
            param_count += 1
            base_query += f" OFFSET ${param_count}"
            params.append(offset)
            
            # Execute queries
            total_count = await conn.fetchval(count_query, *params[:-2])  # Exclude LIMIT and OFFSET params
            rows = await conn.fetch(base_query, *params)
            
            # Process results
            notifications = []
            for row in rows:
                notification = dict(row)
                # Convert datetime objects to ISO format for JSON serialization
                if notification.get("created_at"):
                    notification["created_at"] = notification["created_at"].isoformat()
                if notification.get("read_at"):
                    notification["read_at"] = notification["read_at"].isoformat()
                if notification.get("scheduled_at"):
                    notification["scheduled_at"] = notification["scheduled_at"].isoformat()
                notifications.append(notification)
            
            # Calculate pagination info
            total_pages = (total_count + page_size - 1) // page_size
            
            result = {
                "notifications": notifications,
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
            
            logger.info(f"[NOTIFICATION MANAGER] Retrieved {len(notifications)} notifications out of {total_count} total")
            return result
