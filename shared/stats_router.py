"""
General Statistics Router
Provides endpoints for accessing platform statistics and analytics
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional, Literal
from .utils import GeneralStats
from .response import success_response, error_response
from modules.auth.utils import get_current_admin

router = APIRouter()

@router.get("/platform")
async def get_platform_stats(current_admin: dict = Depends(get_current_admin)):
    """
    Get comprehensive platform statistics (Admin only)
    """
    try:
        stats = await GeneralStats.get_platform_stats()
        return success_response(
            data=stats, 
            message="Platform statistics retrieved successfully"
        )
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/dashboard")
async def get_dashboard_stats(current_admin: dict = Depends(get_current_admin)):
    """
    Get simplified dashboard statistics (Admin only)
    """
    try:
        stats = await GeneralStats.get_dashboard_stats()
        return success_response(
            data=stats, 
            message="Dashboard statistics retrieved successfully"
        )
    except Exception as e:
        return error_response(str(e), status_code=500)

@router.get("/revenue")
async def get_revenue_analytics(
    year: Optional[int] = Query(
        None, description="Year to analyze (defaults to current year)"
    ),
    filter_by: Literal["month", "week", "year"] = Query(
        "month", description="Filter revenue by 'month' (default), 'week', or 'year'"
    ),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get detailed revenue analytics (Admin only)
    """
    try:
        analytics = await GeneralStats.get_revenue_analytics(year, filter_by)
        return success_response(
            data=analytics, 
            message=f"Revenue analytics for {analytics['year']} ({filter_by}) retrieved successfully"
        )
    except Exception as e:
        return error_response(str(e), status_code=500)
