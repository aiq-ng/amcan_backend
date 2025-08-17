"""
General Statistics Utility Functions
Provides comprehensive analytics and statistics for the platform
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Literal
from shared.db import db

logger = logging.getLogger(__name__)

class GeneralStats:
    """General statistics and analytics for the platform"""

    @staticmethod
    async def get_platform_stats() -> Dict[str, Any]:
        """
        Get comprehensive platform statistics

        Returns:
            Dictionary containing:
            - total_patients: Count of registered patients
            - total_doctors: Count of registered doctors
            - total_subscribed_patients: Count of patients with active subscriptions
            - total_video_call_sessions: Count of all video call sessions
            - top_doctors: Top 5 doctors with highest video call sessions
            - recent_notifications: 5 most recent notifications
            - monthly_revenue: Total revenue by month for the current year (Jan-Dec, zero-filled)
        """
        logger.info("[GENERAL STATS] Getting comprehensive platform statistics")

        try:
            async with db.get_connection() as conn:
                # Get basic counts
                total_patients = await conn.fetchval("SELECT COUNT(*) FROM patients")
                total_doctors = await conn.fetchval("SELECT COUNT(*) FROM doctors")
                total_subscribed_patients = await conn.fetchval(
                    "SELECT COUNT(DISTINCT s.user_id) FROM subscriptions s WHERE s.status = 'active'"
                )
                total_video_call_sessions = await conn.fetchval("SELECT COUNT(*) FROM video_calls")

                # Get top 5 doctors with highest video call sessions
                top_doctors = await conn.fetch("""
                    SELECT 
                        d.id,
                        d.first_name,
                        d.last_name,
                        d.title,
                        d.rating,
                        COUNT(vc.id) as video_call_count
                    FROM doctors d
                    LEFT JOIN video_calls vc ON (d.user_id = vc.initiator_id OR d.user_id = vc.receiver_id)
                    GROUP BY d.id, d.first_name, d.last_name, d.title, d.rating
                    ORDER BY video_call_count DESC
                    LIMIT 5
                """)

                # Get 5 most recent notifications
                recent_notifications = await conn.fetch("""
                    SELECT 
                        n.id,
                        n.title,
                        n.message,
                        n.notification_type,
                        n.status,
                        n.priority,
                        n.created_at,
                        u.email as user_email,
                        p.first_name,
                        p.last_name
                    FROM notifications n
                    JOIN users u ON n.user_id = u.id
                    LEFT JOIN patients p ON p.user_id = u.id
                    ORDER BY n.created_at DESC
                    LIMIT 5
                """)

                # Get monthly revenue for current year (Jan-Dec, zero-filled)
                current_year = datetime.now().year
                monthly_revenue_raw = await conn.fetch("""
                    SELECT 
                        EXTRACT(MONTH FROM s.created_at) as month,
                        COUNT(*) as subscription_count,
                        COALESCE(SUM(sp.price), 0) as total_revenue,
                        sp.currency
                    FROM subscriptions s
                    LEFT JOIN subscription_plans sp ON s.plan_id = sp.id
                    WHERE EXTRACT(YEAR FROM s.created_at) = $1
                    AND s.status = 'active'
                    GROUP BY EXTRACT(MONTH FROM s.created_at), sp.currency
                """, current_year)

                # Fill months Jan-Dec, even if zero
                monthly_revenue_map = {int(row["month"]): row for row in monthly_revenue_raw}
                monthly_revenue_list = []
                for m in range(1, 13):
                    row = monthly_revenue_map.get(m)
                    month_name = datetime(current_year, m, 1).strftime("%B")
                    monthly_revenue_list.append({
                        "month": month_name,
                        "month_number": m,
                        "year": current_year,
                        "subscription_count": row["subscription_count"] if row else 0,
                        "total_revenue": float(row["total_revenue"]) if row else 0.0,
                        "currency": (row["currency"] if row and row["currency"] else "NGN")
                    })

                # Calculate additional metrics
                active_subscriptions = await conn.fetchval(
                    "SELECT COUNT(*) FROM subscriptions WHERE status = 'active'"
                )

                total_revenue_current_year = await conn.fetchval("""
                    SELECT COALESCE(SUM(sp.price), 0) 
                    FROM subscriptions s
                    LEFT JOIN subscription_plans sp ON s.plan_id = sp.id
                    WHERE EXTRACT(YEAR FROM s.created_at) = $1 AND s.status = 'active'
                """, current_year)

                # Get platform growth metrics
                current_month = datetime.now().month
                new_patients_this_month = await conn.fetchval("""
                    SELECT COUNT(*) FROM patients 
                    WHERE EXTRACT(MONTH FROM created_at) = $1 AND EXTRACT(YEAR FROM created_at) = $2
                """, current_month, current_year)

                new_doctors_this_month = await conn.fetchval("""
                    SELECT COUNT(*) FROM doctors 
                    WHERE EXTRACT(MONTH FROM created_at) = $1 AND EXTRACT(YEAR FROM created_at) = $2
                """, current_month, current_year)

                video_calls_this_month = await conn.fetchval("""
                    SELECT COUNT(*) FROM video_calls 
                    WHERE EXTRACT(MONTH FROM created_at) = $1 AND EXTRACT(YEAR FROM created_at) = $2
                """, current_month, current_year)

                # Process results
                top_doctors_list = [{
                    "id": doctor["id"],
                    "name": f"{doctor['first_name']} {doctor['last_name']}",
                    "title": doctor["title"],
                    "rating": float(doctor["rating"]) if doctor["rating"] else 0.0,
                    "video_call_count": doctor["video_call_count"]
                } for doctor in top_doctors]

                recent_notifications_list = [{
                    "id": notification["id"],
                    "title": notification["title"],
                    "message": notification["message"],
                    "notification_type": notification["notification_type"],
                    "status": notification["status"],
                    "priority": notification["priority"],
                    "created_at": notification["created_at"].isoformat() if notification["created_at"] else None,
                    "user_email": notification["user_email"],
                    "user_name": f"{notification['first_name']} {notification['last_name']}" if notification["first_name"] and notification["last_name"] else "Unknown"
                } for notification in recent_notifications]

                stats = {
                    "basic_counts": {
                        "total_patients": total_patients,
                        "total_doctors": total_doctors,
                        "total_subscribed_patients": total_subscribed_patients,
                        "total_video_call_sessions": total_video_call_sessions,
                        "active_subscriptions": active_subscriptions
                    },
                    "top_doctors": top_doctors_list,
                    "recent_notifications": recent_notifications_list,
                    "monthly_revenue": monthly_revenue_list,
                    "financial_summary": {
                        "total_revenue_current_year": float(total_revenue_current_year) if total_revenue_current_year else 0.0,
                        "currency": "NGN"
                    },
                    "growth_metrics": {
                        "new_patients_this_month": new_patients_this_month,
                        "new_doctors_this_month": new_doctors_this_month,
                        "video_calls_this_month": video_calls_this_month
                    },
                    "generated_at": datetime.now().isoformat()
                }

                logger.info(f"[GENERAL STATS] Successfully retrieved platform statistics")
                return stats

        except Exception as e:
            logger.error(f"[GENERAL STATS] Error getting platform statistics: {str(e)}")
            raise Exception(f"Failed to get platform statistics: {str(e)}")

    @staticmethod
    async def get_dashboard_stats() -> Dict[str, Any]:
        """
        Get simplified dashboard statistics for quick overview

        Returns:
            Dictionary containing key metrics for dashboard display
        """
        logger.info("[GENERAL STATS] Getting dashboard statistics")

        try:
            async with db.get_connection() as conn:
                # Get key metrics
                total_patients = await conn.fetchval("SELECT COUNT(*) FROM patients")
                total_doctors = await conn.fetchval("SELECT COUNT(*) FROM doctors")
                active_subscriptions = await conn.fetchval(
                    "SELECT COUNT(*) FROM subscriptions WHERE status = 'active'"
                )
                total_video_calls = await conn.fetchval("SELECT COUNT(*) FROM video_calls")

                # Get today's metrics
                today = datetime.now().date()
                new_patients_today = await conn.fetchval("""
                    SELECT COUNT(*) FROM patients 
                    WHERE DATE(created_at) = $1
                """, today)

                new_doctors_today = await conn.fetchval("""
                    SELECT COUNT(*) FROM doctors 
                    WHERE DATE(created_at) = $1
                """, today)

                video_calls_today = await conn.fetchval("""
                    SELECT COUNT(*) FROM video_calls 
                    WHERE DATE(created_at) = $1
                """, today)

                # Get this month's revenue
                current_month = datetime.now().month
                current_year = datetime.now().year
                monthly_revenue = await conn.fetchval("""
                    SELECT COALESCE(SUM(sp.price), 0) 
                    FROM subscriptions s
                    LEFT JOIN subscription_plans sp ON s.plan_id = sp.id
                    WHERE EXTRACT(MONTH FROM s.created_at) = $1 
                    AND EXTRACT(YEAR FROM s.created_at) = $2 
                    AND s.status = 'active'
                """, current_month, current_year)

                dashboard_stats = {
                    "overview": {
                        "total_patients": total_patients,
                        "total_doctors": total_doctors,
                        "active_subscriptions": active_subscriptions,
                        "total_video_calls": total_video_calls
                    },
                    "today": {
                        "new_patients": new_patients_today,
                        "new_doctors": new_doctors_today,
                        "video_calls": video_calls_today
                    },
                    "this_month": {
                        "revenue": float(monthly_revenue) if monthly_revenue else 0.0,
                        "currency": "NGN"
                    },
                    "generated_at": datetime.now().isoformat()
                }

                logger.info(f"[GENERAL STATS] Successfully retrieved dashboard statistics")
                return dashboard_stats

        except Exception as e:
            logger.error(f"[GENERAL STATS] Error getting dashboard statistics: {str(e)}")
            raise Exception(f"Failed to get dashboard statistics: {str(e)}")

    @staticmethod
    async def get_revenue_analytics(
        year: Optional[int] = None,
        filter_by: Literal["month", "week", "year"] = "month"
    ) -> Dict[str, Any]:
        """
        Get detailed revenue analytics, filterable by month, week, or year.

        Args:
            year: Year to analyze (defaults to current year)
            filter_by: "month" (default, Jan-Dec), "week" (last 7 days), or "year" (total)

        Returns:
            Dictionary containing revenue analytics
        """
        if year is None:
            year = datetime.now().year

        logger.info(f"[GENERAL STATS] Getting revenue analytics for year {year}, filter: {filter_by}")

        try:
            async with db.get_connection() as conn:
                analytics = {
                    "year": year,
                    "currency": "NGN",
                    "monthly_breakdown": [],
                    "weekly_breakdown": [],
                    "yearly_breakdown": [],
                    "plan_breakdown": [],
                    "total_revenue": 0.0,
                    "generated_at": datetime.now().isoformat()
                }

                # Monthly breakdown (Jan-Dec, zero-filled)
                if filter_by == "month" or filter_by == "year":
                    monthly_data = await conn.fetch("""
                        SELECT 
                            EXTRACT(MONTH FROM s.created_at) as month,
                            COUNT(*) as subscription_count,
                            COALESCE(SUM(sp.price), 0) as revenue,
                            sp.currency
                        FROM subscriptions s
                        LEFT JOIN subscription_plans sp ON s.plan_id = sp.id
                        WHERE EXTRACT(YEAR FROM s.created_at) = $1
                        AND s.status = 'active'
                        GROUP BY EXTRACT(MONTH FROM s.created_at), sp.currency
                    """, year)
                    monthly_map = {int(row["month"]): row for row in monthly_data}
                    monthly_breakdown = []
                    for m in range(1, 13):
                        row = monthly_map.get(m)
                        month_name = datetime(year, m, 1).strftime("%B")
                        monthly_breakdown.append({
                            "month": month_name,
                            "month_number": m,
                            "subscription_count": row["subscription_count"] if row else 0,
                            "revenue": float(row["revenue"]) if row else 0.0,
                            "currency": (row["currency"] if row and row["currency"] else "NGN")
                        })
                    analytics["monthly_breakdown"] = monthly_breakdown

                # Weekly breakdown (last 7 days, zero-filled)
                if filter_by == "week":
                    today = datetime.now().date()
                    # Generate last 7 days list (Mon-Sun style, depending on today)
                    week_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
                    week_map = {}

                    week_data = await conn.fetch("""
                        SELECT 
                            DATE(s.created_at) as day,
                            COUNT(*) as subscription_count,
                            COALESCE(SUM(sp.price), 0) as revenue,
                            sp.currency
                        FROM subscriptions s
                        LEFT JOIN subscription_plans sp ON s.plan_id = sp.id
                        WHERE s.created_at >= $1
                        AND s.created_at < $2
                        AND s.status = 'active'
                        GROUP BY day, sp.currency
                    """, week_days[0], today + timedelta(days=1))

                    for row in week_data:
                        week_map[row["day"]] = row

                    weekly_breakdown = []
                    for d in week_days:
                        row = week_map.get(d)
                        weekly_breakdown.append({
                            "date": d.isoformat(),
                            "day": d.strftime("%a"),  # 👈 Add short weekday name
                            "subscription_count": row["subscription_count"] if row else 0,
                            "revenue": float(row["revenue"]) if row else 0.0,
                            "currency": (row["currency"] if row and row["currency"] else "NGN")
                        })

                    analytics["weekly_breakdown"] = weekly_breakdown


                # Yearly breakdown (total for the year)
                if filter_by == "year":
                    yearly_revenue = await conn.fetchval("""
                        SELECT COALESCE(SUM(sp.price), 0) 
                        FROM subscriptions s
                        LEFT JOIN subscription_plans sp ON s.plan_id = sp.id
                        WHERE EXTRACT(YEAR FROM s.created_at) = $1 AND s.status = 'active'
                    """, year)
                    analytics["yearly_breakdown"] = [{
                        "year": year,
                        "revenue": float(yearly_revenue) if yearly_revenue else 0.0,
                        "currency": "NGN"
                    }]
                    analytics["total_revenue"] = float(yearly_revenue) if yearly_revenue else 0.0
                else:
                    # For month/week, sum up the revenue
                    if filter_by == "month":
                        analytics["total_revenue"] = sum(m["revenue"] for m in analytics["monthly_breakdown"])
                    elif filter_by == "week":
                        analytics["total_revenue"] = sum(w["revenue"] for w in analytics["weekly_breakdown"])

                # Plan-wise breakdown (always for the year)
                plan_data = await conn.fetch("""
                    SELECT 
                        s.subscription_type,
                        COUNT(*) as subscription_count,
                        COALESCE(SUM(sp.price), 0) as revenue,
                        sp.currency
                    FROM subscriptions s
                    LEFT JOIN subscription_plans sp ON s.plan_id = sp.id
                    WHERE EXTRACT(YEAR FROM s.created_at) = $1
                    AND s.status = 'active'
                    GROUP BY s.subscription_type, sp.currency
                    ORDER BY revenue DESC
                """, year)
                analytics["plan_breakdown"] = [{
                    "plan_type": data["subscription_type"],
                    "subscription_count": data["subscription_count"],
                    "revenue": float(data["revenue"]) if data["revenue"] else 0.0,
                    "currency": data["currency"] or "NGN"
                } for data in plan_data]

                logger.info(f"[GENERAL STATS] Successfully retrieved revenue analytics for {year} ({filter_by})")
                return analytics

        except Exception as e:
            logger.error(f"[GENERAL STATS] Error getting revenue analytics: {str(e)}")
            raise Exception(f"Failed to get revenue analytics: {str(e)}")
