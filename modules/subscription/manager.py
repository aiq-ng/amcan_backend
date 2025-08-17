import logging
from datetime import datetime, timedelta
from typing import List, Optional
from .models import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse, SubscriptionPlan, SubscriptionStatus, SubscriptionType
from shared.db import db

logger = logging.getLogger(__name__)

class SubscriptionManager:
    @staticmethod
    async def create_subscription(subscription_data: SubscriptionCreate) -> dict:
        """Create a new subscription for a user"""
        logger.info(f"[SUBSCRIPTION MANAGER] Creating subscription for user: {subscription_data.user_id}")
        
        async with db.get_connection() as conn:
            # Set default dates if not provided
            start_date = subscription_data.start_date or datetime.utcnow()
            end_date = subscription_data.end_date or (start_date + timedelta(days=30))
            
            result = await conn.fetchrow(
                """
                INSERT INTO subscriptions (user_id, subscription_type, status, start_date, end_date, auto_renew, payment_method)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, user_id, subscription_type, status, start_date, end_date, auto_renew, payment_method, created_at, updated_at
                """,
                subscription_data.user_id,
                subscription_data.subscription_type,
                SubscriptionStatus.ACTIVE,
                start_date,
                end_date,
                subscription_data.auto_renew,
                subscription_data.payment_method
            )
            
            logger.info(f"[SUBSCRIPTION MANAGER] Subscription created successfully: {result['id']}")
            return dict(result)

    @staticmethod
    async def get_user_subscription(user_id: int) -> Optional[dict]:
        """Get the current active subscription for a user"""
        logger.info(f"[SUBSCRIPTION MANAGER] Getting subscription for user: {user_id}")
        
        async with db.get_connection() as conn:
            result = await conn.fetchrow(
                """
                SELECT id, user_id, subscription_type, status, start_date, end_date, auto_renew, payment_method, created_at, updated_at
                FROM subscriptions
                WHERE user_id = $1 AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                user_id
            )
            
            if result:
                logger.info(f"[SUBSCRIPTION MANAGER] Found active subscription: {result['id']}")
                return dict(result)
            else:
                logger.info(f"[SUBSCRIPTION MANAGER] No active subscription found for user: {user_id}")
                return None

    @staticmethod
    async def update_subscription(subscription_id: int, update_data: SubscriptionUpdate) -> Optional[dict]:
        """Update an existing subscription"""
        logger.info(f"[SUBSCRIPTION MANAGER] Updating subscription: {subscription_id}")
        
        async with db.get_connection() as conn:
            # Build update query dynamically
            fields = []
            values = []
            
            if update_data.subscription_type is not None:
                fields.append("subscription_type = $%d" % (len(values) + 1))
                values.append(update_data.subscription_type)
            
            if update_data.status is not None:
                fields.append("status = $%d" % (len(values) + 1))
                values.append(update_data.status)
            
            if update_data.end_date is not None:
                fields.append("end_date = $%d" % (len(values) + 1))
                values.append(update_data.end_date)
            
            if update_data.auto_renew is not None:
                fields.append("auto_renew = $%d" % (len(values) + 1))
                values.append(update_data.auto_renew)
            
            if update_data.payment_method is not None:
                fields.append("payment_method = $%d" % (len(values) + 1))
                values.append(update_data.payment_method)
            
            if not fields:
                logger.warning(f"[SUBSCRIPTION MANAGER] No fields to update for subscription: {subscription_id}")
                return None
            
            # Add updated_at timestamp
            fields.append("updated_at = $%d" % (len(values) + 1))
            values.append(datetime.utcnow())
            
            values.append(subscription_id)
            query = f"""
                UPDATE subscriptions 
                SET {', '.join(fields)}
                WHERE id = $%d
                RETURNING id, user_id, subscription_type, status, start_date, end_date, auto_renew, payment_method, created_at, updated_at
            """ % (len(values))
            
            result = await conn.fetchrow(query, *values)
            
            if result:
                logger.info(f"[SUBSCRIPTION MANAGER] Subscription updated successfully: {subscription_id}")
                return dict(result)
            else:
                logger.warning(f"[SUBSCRIPTION MANAGER] Subscription not found: {subscription_id}")
                return None

    @staticmethod
    async def cancel_subscription(subscription_id: int) -> bool:
        """Cancel a subscription"""
        logger.info(f"[SUBSCRIPTION MANAGER] Cancelling subscription: {subscription_id}")
        
        async with db.get_connection() as conn:
            result = await conn.execute(
                """
                UPDATE subscriptions 
                SET status = 'cancelled', updated_at = $1
                WHERE id = $2
                """,
                datetime.utcnow(),
                subscription_id
            )
            
            if result == "UPDATE 1":
                logger.info(f"[SUBSCRIPTION MANAGER] Subscription cancelled successfully: {subscription_id}")
                return True
            else:
                logger.warning(f"[SUBSCRIPTION MANAGER] Failed to cancel subscription: {subscription_id}")
                return False

    @staticmethod
    async def get_subscription_plans() -> List[dict]:
        """Get all available subscription plans"""
        logger.info("[SUBSCRIPTION MANAGER] Getting subscription plans")
        
        async with db.get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, type, price, currency, duration_days, features, is_active
                FROM subscription_plans
                WHERE is_active = true
                ORDER BY price ASC
                """
            )
            
            plans = [dict(row) for row in rows]
            logger.info(f"[SUBSCRIPTION MANAGER] Retrieved {len(plans)} subscription plans")
            return plans

    @staticmethod
    async def check_subscription_expiry() -> List[dict]:
        """Check for subscriptions that are about to expire or have expired"""
        logger.info("[SUBSCRIPTION MANAGER] Checking subscription expiry")
        
        async with db.get_connection() as conn:
            # Get subscriptions expiring in the next 7 days or already expired
            rows = await conn.fetch(
                """
                SELECT id, user_id, subscription_type, end_date, status
                FROM subscriptions
                WHERE status = 'active' 
                AND end_date <= (CURRENT_DATE + INTERVAL '7 days')
                ORDER BY end_date ASC
                """
            )
            
            expiring_subscriptions = [dict(row) for row in rows]
            logger.info(f"[SUBSCRIPTION MANAGER] Found {len(expiring_subscriptions)} expiring subscriptions")
            return expiring_subscriptions

    @staticmethod
    async def get_all_subscriptions(
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        subscription_type: Optional[str] = None,
        plan_id: Optional[int] = None,
        user_search: Optional[str] = None,
        start_date_from: Optional[datetime] = None,
        start_date_to: Optional[datetime] = None,
        end_date_from: Optional[datetime] = None,
        end_date_to: Optional[datetime] = None,
        auto_renew: Optional[bool] = None,
        payment_method: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> dict:
        """
        Get all subscriptions with pagination and filters (Admin only)
        Returns: {subscriptions: List[dict], total_count: int, total_pages: int, current_page: int}
        """
        logger.info(f"[SUBSCRIPTION MANAGER] Getting all subscriptions with filters - page: {page}, page_size: {page_size}")
        
        async with db.get_connection() as conn:
            # Build the base query with filters
            base_query = """
                SELECT 
                    s.id,
                    s.user_id,
                    s.subscription_type,
                    s.status,
                    s.start_date,
                    s.end_date,
                    s.auto_renew,
                    s.payment_method,
                    s.created_at,
                    s.updated_at,
                    u.email as user_email,
                    p.first_name,
                    p.last_name,
                    sp.id as plan_id,
                    sp.name as plan_name,
                    sp.price as plan_price,
                    sp.currency as plan_currency
                FROM subscriptions s
                JOIN users u ON s.user_id = u.id
                LEFT JOIN patients p ON p.user_id = u.id
                LEFT JOIN subscription_plans sp ON s.plan_id = sp.id
                WHERE 1=1
            """
            
            # Build count query
            count_query = """
                SELECT COUNT(*) 
                FROM subscriptions s
                JOIN users u ON s.user_id = u.id
                LEFT JOIN patients p ON p.user_id = u.id
                LEFT JOIN subscription_plans sp ON s.plan_id = sp.id
                WHERE 1=1
            """
            
            # Parameters for both queries
            params = []
            param_count = 0
            
            # Add filters
            if status:
                param_count += 1
                base_query += f" AND s.status = ${param_count}"
                count_query += f" AND s.status = ${param_count}"
                params.append(status)
            
            if subscription_type:
                param_count += 1
                base_query += f" AND s.subscription_type = ${param_count}"
                count_query += f" AND s.subscription_type = ${param_count}"
                params.append(subscription_type)
            
            if plan_id:
                param_count += 1
                base_query += f" AND s.plan_id = ${param_count}"
                count_query += f" AND s.plan_id = ${param_count}"
                params.append(plan_id)
            
            if user_search:
                param_count += 1
                base_query += f" AND (u.email ILIKE ${param_count} OR p.first_name ILIKE ${param_count} OR p.last_name ILIKE ${param_count} OR CONCAT(p.first_name, ' ', p.last_name) ILIKE ${param_count})"
                count_query += f" AND (u.email ILIKE ${param_count} OR p.first_name ILIKE ${param_count} OR p.last_name ILIKE ${param_count} OR CONCAT(p.first_name, ' ', p.last_name) ILIKE ${param_count})"
                params.append(f"%{user_search}%")
            
            if start_date_from:
                param_count += 1
                base_query += f" AND s.start_date >= ${param_count}"
                count_query += f" AND s.start_date >= ${param_count}"
                params.append(start_date_from)
            
            if start_date_to:
                param_count += 1
                base_query += f" AND s.start_date <= ${param_count}"
                count_query += f" AND s.start_date <= ${param_count}"
                params.append(start_date_to)
            
            if end_date_from:
                param_count += 1
                base_query += f" AND s.end_date >= ${param_count}"
                count_query += f" AND s.end_date >= ${param_count}"
                params.append(end_date_from)
            
            if end_date_to:
                param_count += 1
                base_query += f" AND s.end_date <= ${param_count}"
                count_query += f" AND s.end_date <= ${param_count}"
                params.append(end_date_to)
            
            if auto_renew is not None:
                param_count += 1
                base_query += f" AND s.auto_renew = ${param_count}"
                count_query += f" AND s.auto_renew = ${param_count}"
                params.append(auto_renew)
            
            if payment_method:
                param_count += 1
                base_query += f" AND s.payment_method ILIKE ${param_count}"
                count_query += f" AND s.payment_method ILIKE ${param_count}"
                params.append(f"%{payment_method}%")
            
            # Validate sort parameters
            valid_sort_fields = ["id", "user_id", "subscription_type", "status", "start_date", "end_date", "created_at", "updated_at"]
            if sort_by not in valid_sort_fields:
                sort_by = "created_at"
            
            if sort_order.lower() not in ["asc", "desc"]:
                sort_order = "desc"
            
            # Add sorting
            base_query += f" ORDER BY s.{sort_by} {sort_order.upper()}"
            
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
            subscriptions = []
            for row in rows:
                subscription = dict(row)
                # Convert datetime objects to ISO format for JSON serialization
                if subscription.get("start_date"):
                    subscription["start_date"] = subscription["start_date"].isoformat()
                if subscription.get("end_date"):
                    subscription["end_date"] = subscription["end_date"].isoformat()
                if subscription.get("created_at"):
                    subscription["created_at"] = subscription["created_at"].isoformat()
                if subscription.get("updated_at"):
                    subscription["updated_at"] = subscription["updated_at"].isoformat()
                subscriptions.append(subscription)
            
            # Calculate pagination info
            total_pages = (total_count + page_size - 1) // page_size
            
            result = {
                "subscriptions": subscriptions,
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
            
            logger.info(f"[SUBSCRIPTION MANAGER] Retrieved {len(subscriptions)} subscriptions out of {total_count} total")
            return result
