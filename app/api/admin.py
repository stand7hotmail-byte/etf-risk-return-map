"""
Admin API endpoints for managing and retrieving affiliate performance statistics.
"""
from datetime import datetime, timedelta
from functools import lru_cache
from typing import List, Optional

from app.db.database import get_db
from app.models.affiliate import AffiliateBroker, AffiliateClick
from app.schemas import (AffiliateStatsResponse, BrokerPerformanceStats,
                         DailyPerformanceStats, ManualConversionRequest,
                         PlacementPerformanceStats, TopPerformingBroker)
from fastapi import APIRouter, Depends, HTTPException, status, Request # Requestを追加
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from slowapi import Limiter # 追加
from app.dependencies import get_rate_limiter, get_admin_user # get_rate_limiter, get_admin_userを追加


# Placeholder for admin user dependency.
# In a real application, this would verify the user's authentication
# and authorization (e.g., check for an 'admin' role).
def get_admin_user_placeholder(): # 名前を変更して衝突を避ける
    """
    Placeholder dependency to simulate admin authentication.
    Raises HTTPException if user is not considered an admin.
    """
    # For now, we'll allow access, but in production, this should check
    # a proper authentication token and user roles.
    # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return {"username": "admin", "id": "admin_user_id"}


router = APIRouter(prefix="/api/admin/affiliate", tags=["Admin Affiliate"])

# In-memory cache for aggregate statistics
# In a production environment, consider a more robust caching solution like Redis.
@lru_cache(maxsize=1) # Cache only the most recent call
def get_cached_affiliate_stats(start_date: datetime, end_date: datetime, db: Session):
    """Caches the affiliate statistics."""
    # Ensure timezone awareness if your DB stores timezone info
    start_date_dt = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date_dt = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    total_clicks_query = db.query(AffiliateClick).filter(
        AffiliateClick.clicked_at >= start_date_dt,
        AffiliateClick.clicked_at <= end_date_dt
    )
    total_clicks = total_clicks_query.count()

    total_conversions_query = db.query(AffiliateClick).filter(
        AffiliateClick.converted == True,
        AffiliateClick.converted_at >= start_date_dt,
        AffiliateClick.converted_at <= end_date_dt
    )
    total_conversions = total_conversions_query.count()

    conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0.0

    # Broker performance
    broker_stats_query = db.query(
        AffiliateBroker.broker_name,
        AffiliateBroker.display_name,
        func.count(AffiliateClick.id).label("clicks"),
        func.sum(case((AffiliateClick.converted == True, 1), else_=0)).label("conversions"),
        func.sum(case((AffiliateClick.converted == True, AffiliateBroker.commission_rate), else_=0)).label("revenue")
    ).join(AffiliateBroker, AffiliateClick.broker_id == AffiliateBroker.id).filter(
        AffiliateClick.clicked_at >= start_date_dt,
        AffiliateClick.clicked_at <= end_date_dt
    ).group_by(AffiliateBroker.broker_name, AffiliateBroker.display_name).all()

    by_broker = []
    estimated_total_revenue = 0.0
    for stat in broker_stats_query:
        broker_clicks = stat.clicks or 0
        broker_conversions = stat.conversions or 0
        broker_conversion_rate = (broker_conversions / broker_clicks * 100) if broker_clicks > 0 else 0.0
        broker_revenue = stat.revenue or 0.0
        by_broker.append(
            BrokerPerformanceStats(
                broker_name=stat.broker_name,
                clicks=broker_clicks,
                conversions=broker_conversions,
                conversion_rate=broker_conversion_rate,
                revenue=broker_revenue
            )
        )
        estimated_total_revenue += broker_revenue
    
    # Placement performance
    placement_stats_query = db.query(
        AffiliateClick.placement,
        func.count(AffiliateClick.id).label("clicks"),
        func.sum(case((AffiliateClick.converted == True, 1), else_=0)).label("conversions")
    ).filter(
        AffiliateClick.clicked_at >= start_date_dt,
        AffiliateClick.clicked_at <= end_date_dt
    ).group_by(AffiliateClick.placement).all()

    by_placement = []
    for stat in placement_stats_query:
        placement_clicks = stat.clicks or 0
        placement_conversions = stat.conversions or 0
        placement_conversion_rate = (placement_conversions / placement_clicks * 100) if placement_clicks > 0 else 0.0
        by_placement.append(
            PlacementPerformanceStats(
                placement=stat.placement,
                clicks=placement_clicks,
                conversions=placement_conversions,
                conversion_rate=placement_conversion_rate
            )
        )

    # Daily performance for charts
    daily_stats_query = db.query(
        func.date(AffiliateClick.clicked_at).label("date"),
        func.count(AffiliateClick.id).label("clicks"),
        func.sum(case((AffiliateClick.converted == True, 1), else_=0)).label("conversions")
    ).filter(
        AffiliateClick.clicked_at >= start_date_dt,
        AffiliateClick.clicked_at <= end_date_dt
    ).group_by(func.date(AffiliateClick.clicked_at)).order_by(func.date(AffiliateClick.clicked_at)).all()

    daily_performance = []
    # Create a dictionary for quick lookups
    stats_dict = {
        stat.date: {
            "clicks": stat.clicks or 0,
            "conversions": stat.conversions or 0
        }
        for stat in daily_stats_query
    }
    
    # Ensure all days in the range are present
    current_date = start_date_dt.date()
    end_date_date = end_date_dt.date()
    while current_date <= end_date_date:
        date_str = current_date.isoformat()
        day_stats = stats_dict.get(date_str, {"clicks": 0, "conversions": 0})
        daily_performance.append(
            DailyPerformanceStats(
                date=date_str,
                clicks=day_stats["clicks"],
                conversions=day_stats["conversions"]
            )
        )
        current_date += timedelta(days=1)


    return AffiliateStatsResponse(
        period={"start": start_date_dt, "end": end_date_dt},
        total_clicks=total_clicks,
        total_conversions=total_conversions,
        conversion_rate=conversion_rate,
        estimated_revenue=estimated_total_revenue,
        by_broker=by_broker,
        by_placement=by_placement,
        daily_performance=daily_performance
    )


@router.get(
    "/stats",
    response_model=AffiliateStatsResponse,
    summary="Get overall affiliate statistics",
    description="Retrieves aggregated affiliate clicks, conversions, conversion rates, and estimated revenue for a specified period."
)
@limiter.limit("100/minute") # レート制限を追加
async def get_affiliate_stats(
    request: Request, # Requestを追加
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user), # Admin auth (コメントアウトを外す)
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limiter: Limiter = Depends(get_rate_limiter) # Limiterを追加
) -> AffiliateStatsResponse:
    """
    Get overall affiliate statistics for a given period.

    Args:
        request: The FastAPI request object for rate limiting.
        db: The database session.
        admin_user: Authenticated admin user (from dependency).
        start_date: Optional. Start date for aggregation (defaults to 30 days ago).
        end_date: Optional. End date for aggregation (defaults to today).
        limiter: The rate limiter instance.

    Returns:
        AffiliateStatsResponse: Aggregated statistics.
    """
    if end_date is None:
        end_date = datetime.utcnow()
    if start_date is None:
        start_date = end_date - timedelta(days=30)
    
    # Clear cache before calling if fresh data is always desired.
    # For a cache with TTL, no need to clear manually unless forced.
    # get_cached_affiliate_stats.cache_clear() 
    
    return get_cached_affiliate_stats(start_date, end_date, db)


@router.get(
    "/top-performing",
    response_model=List[TopPerformingBroker],
    summary="Get top-performing affiliate brokers",
    description="Retrieves a list of affiliate brokers ranked by a specified metric (clicks, conversions, or revenue)."
)
@limiter.limit("100/minute") # レート制限を追加
async def get_top_performing_brokers(
    request: Request, # Requestを追加
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user), # Admin auth (コメントアウトを外す)
    metric: str = "conversions", # clicks/conversions/revenue
    limit: int = 5,
    limiter: Limiter = Depends(get_rate_limiter) # Limiterを追加
) -> List[TopPerformingBroker]:
    """
    Get top-performing affiliate brokers based on a given metric.

    Args:
        request: The FastAPI request object for rate limiting.
        db: The database session.
        admin_user: Authenticated admin user (from dependency).
        metric: Metric to rank by ('clicks', 'conversions', 'revenue').
        limit: Number of top brokers to return.
        limiter: The rate limiter instance.
    Returns:
        List[TopPerformingBroker]: List of top brokers with their stats.
    """
    if metric not in ["clicks", "conversions", "revenue"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid metric. Must be one of 'clicks', 'conversions', 'revenue'."
        )

    # Subquery to calculate stats for each broker
    broker_stats_subquery = db.query(
        AffiliateBroker.id,
        AffiliateBroker.broker_name,
        AffiliateBroker.display_name,
        func.count(AffiliateClick.id).label("clicks"),
        func.sum(case( # Corrected: Use sum(case) for conversions
            (AffiliateClick.converted == True, 1), # Count 1 for each converted click
            else_=0
        )).label("conversions"),
        func.sum(
            case( # Corrected: 'whens' argument should not be a list
                (AffiliateClick.converted == True, AffiliateBroker.commission_rate),
                else_=0
            )
        ).label("revenue")
    ).join(AffiliateBroker, AffiliateClick.broker_id == AffiliateBroker.id).group_by(
        AffiliateBroker.id, AffiliateBroker.broker_name, AffiliateBroker.display_name
    ).subquery()
    
    # Order by the specified metric
    if metric == "clicks":
        order_by_col = broker_stats_subquery.c.clicks
    elif metric == "conversions":
        order_by_col = broker_stats_subquery.c.conversions
    else: # revenue
        order_by_col = broker_stats_subquery.c.revenue

    top_brokers_query = db.query(broker_stats_subquery).order_by(order_by_col.desc()).limit(limit)
    top_brokers = top_brokers_query.all()

    result = []
    for broker in top_brokers:
        clicks = broker.clicks
        conversions = broker.conversions
        conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0.0
        revenue = broker.revenue if broker.revenue else 0.0
        result.append(
            TopPerformingBroker(
                broker_id=broker.id,
                broker_name=broker.broker_name,
                display_name=broker.display_name,
                clicks=clicks,
                conversions=conversions,
                conversion_rate=conversion_rate,
                revenue=revenue
            )
        )
    return result


@router.post(
    "/conversions",
    summary="Manually record an affiliate conversion",
    description="Allows administrators to manually mark an affiliate click as converted, updating its status and conversion timestamp."
)
@limiter.limit("30/minute") # レート制限を追加 (管理者だが、POST操作のためやや厳しく)
async def record_manual_conversion(
    request: Request, # Requestを追加
    conversion_data: ManualConversionRequest,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user), # Admin auth (コメントアウトを外す)
    limiter: Limiter = Depends(get_rate_limiter) # Limiterを追加
) -> dict:
    """
    Manually record an affiliate conversion.

    Args:
        request: The FastAPI request object for rate limiting.
        conversion_data: The conversion data, including click_id.
        db: The database session.
        admin_user: Authenticated admin user (from dependency).
        limiter: The rate limiter instance.

    Returns:
        A dictionary indicating success.
    """
    click = db.query(AffiliateClick).filter(
        AffiliateClick.id == conversion_data.click_id
    ).first()

    if not click:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Affiliate click with ID {conversion_data.click_id} not found."
        )

    if click.converted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Affiliate click with ID {conversion_data.click_id} is already marked as converted."
        )

    click.converted = True
    click.converted_at = conversion_data.converted_at if conversion_data.converted_at else datetime.utcnow()
    
    db.add(click)
    db.commit()
    db.refresh(click)

    return {"success": True, "message": f"Click {click.id} marked as converted."}
