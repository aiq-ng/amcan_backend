from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from .models import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse, SubscriptionPlan
from .manager import SubscriptionManager
from modules.auth.utils import get_current_user, get_current_admin
from shared.response import success_response, error_response

router = APIRouter()

@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new subscription (Admin only)"""
    try:
        subscription = await SubscriptionManager.create_subscription(subscription_data)
        return success_response(data=subscription, message="Subscription created successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/me")
async def get_my_subscription(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription"""
    try:
        subscription = await SubscriptionManager.get_user_subscription(current_user["id"])
        if not subscription:
            return success_response(data=None, message="No active subscription found")
        return success_response(data=subscription, message="Subscription retrieved successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/{subscription_id}")
async def get_subscription(
    subscription_id: int,
    current_admin: dict = Depends(get_current_admin)
):
    """Get a specific subscription (Admin only)"""
    try:
        # This would need to be implemented in the manager
        # For now, returning a placeholder
        return success_response(data={"id": subscription_id}, message="Subscription retrieved successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.put("/{subscription_id}")
async def update_subscription(
    subscription_id: int,
    update_data: SubscriptionUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update a subscription (Admin only)"""
    try:
        subscription = await SubscriptionManager.update_subscription(subscription_id, update_data)
        if not subscription:
            return error_response("Subscription not found", status_code=404)
        return success_response(data=subscription, message="Subscription updated successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.delete("/{subscription_id}")
async def cancel_subscription(
    subscription_id: int,
    current_admin: dict = Depends(get_current_admin)
):
    """Cancel a subscription (Admin only)"""
    try:
        success = await SubscriptionManager.cancel_subscription(subscription_id)
        if not success:
            return error_response("Failed to cancel subscription", status_code=500)
        return success_response(data=None, message="Subscription cancelled successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/plans/available")
async def get_available_plans():
    """Get all available subscription plans"""
    try:
        plans = await SubscriptionManager.get_subscription_plans()
        return success_response(data=plans, message="Subscription plans retrieved successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/admin/all")
async def get_all_subscriptions_admin(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    status: Optional[str] = Query(None, description="Filter by subscription status"),
    subscription_type: Optional[str] = Query(None, description="Filter by subscription type"),
    plan_id: Optional[int] = Query(None, description="Filter by subscription plan ID"),
    user_search: Optional[str] = Query(None, description="Search by user email, first name, last name, or full name (partial match)"),
    start_date_from: Optional[str] = Query(None, description="Filter by start date from (YYYY-MM-DD)"),
    start_date_to: Optional[str] = Query(None, description="Filter by start date to (YYYY-MM-DD)"),
    end_date_from: Optional[str] = Query(None, description="Filter by end date from (YYYY-MM-DD)"),
    end_date_to: Optional[str] = Query(None, description="Filter by end date to (YYYY-MM-DD)"),
    auto_renew: Optional[bool] = Query(None, description="Filter by auto-renew status"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method (partial match)"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get all subscriptions with pagination and filters (Admin only)
    
    Available filters:
    - status: active, inactive, expired, cancelled, pending
    - subscription_type: basic, premium, enterprise
    - plan_id: filter by specific subscription plan ID
    - user_search: search by email, first name, last name, or full name (partial match)
    - start_date_from/start_date_to: date range for start date
    - end_date_from/end_date_to: date range for end date
    - auto_renew: true/false
    - payment_method: partial match
    
    Available sort fields:
    - id, user_id, subscription_type, status, start_date, end_date, created_at, updated_at
    
    Sort order: asc or desc
    """
    try:
        # Parse date strings to datetime objects
        start_date_from_dt = None
        start_date_to_dt = None
        end_date_from_dt = None
        end_date_to_dt = None
        
        if start_date_from:
            try:
                # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS formats
                if 'T' in start_date_from:
                    start_date_from_dt = datetime.fromisoformat(start_date_from)
                else:
                    start_date_from_dt = datetime.strptime(start_date_from, "%Y-%m-%d")
            except ValueError:
                return error_response("Invalid start_date_from format. Use YYYY-MM-DD", status_code=400)
        
        if start_date_to:
            try:
                # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS formats
                if 'T' in start_date_to:
                    start_date_to_dt = datetime.fromisoformat(start_date_to)
                else:
                    start_date_to_dt = datetime.strptime(start_date_to, "%Y-%m-%d")
            except ValueError:
                return error_response("Invalid start_date_to format. Use YYYY-MM-DD", status_code=400)
        
        if end_date_from:
            try:
                # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS formats
                if 'T' in end_date_from:
                    end_date_from_dt = datetime.fromisoformat(end_date_from)
                else:
                    end_date_from_dt = datetime.strptime(end_date_from, "%Y-%m-%d")
            except ValueError:
                return error_response("Invalid end_date_from format. Use YYYY-MM-DD", status_code=400)
        
        if end_date_to:
            try:
                # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS formats
                if 'T' in end_date_to:
                    end_date_to_dt = datetime.fromisoformat(end_date_to)
                else:
                    end_date_to_dt = datetime.strptime(end_date_to, "%Y-%m-%d")
            except ValueError:
                return error_response("Invalid end_date_to format. Use YYYY-MM-DD", status_code=400)
        
        result = await SubscriptionManager.get_all_subscriptions(
            page=page,
            page_size=page_size,
            status=status,
            subscription_type=subscription_type,
            plan_id=plan_id,
            user_search=user_search,
            start_date_from=start_date_from_dt,
            start_date_to=start_date_to_dt,
            end_date_from=end_date_from_dt,
            end_date_to=end_date_to_dt,
            auto_renew=auto_renew,
            payment_method=payment_method,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return success_response(
            data=result, 
            message=f"Retrieved {len(result['subscriptions'])} subscriptions (page {page} of {result['total_pages']})"
        )
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/admin/expiring")
async def get_expiring_subscriptions(current_admin: dict = Depends(get_current_admin)):
    """Get subscriptions that are expiring soon (Admin only)"""
    try:
        expiring = await SubscriptionManager.check_subscription_expiry()
        return success_response(data=expiring, message="Expiring subscriptions retrieved successfully")
    except Exception as e:
        return error_response(str(e), status_code=500)
