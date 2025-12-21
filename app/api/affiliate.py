# -*- coding: utf-8 -*-
"""
API endpoints for managing and interacting with affiliate brokers and tracking clicks.
"""
import json
from typing import List, Optional
from datetime import datetime # Added missing import

from app.db.database import get_db
from app.models.affiliate import AffiliateBroker, AffiliateClick
from app.schemas import (AffiliateBroker as SchemaAffiliateBroker,
                         AffiliateClick as SchemaAffiliateClick,
                         BrokerRecommendationQuery, TrackClickRequest)
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from slowapi import Limiter # 追加
from app.dependencies import get_rate_limiter # 追加

# from app.dependencies import get_current_user_id # Placeholder for user ID retrieval

router = APIRouter(prefix="/api", tags=["Affiliate"])


@router.get(
    "/brokers",
    response_model=List[SchemaAffiliateBroker],
    summary="Get a list of affiliate brokers",
    description="Retrieve a list of affiliate brokerage firms, with optional filtering by region and activity status."
)
@limiter.limit("60/minute") # レート制限を追加
async def get_brokers(
    request: Request, # Requestを追加
    db: Session = Depends(get_db),
    region: Optional[str] = None,
    active_only: bool = True,
    limiter: Limiter = Depends(get_rate_limiter) # Limiterを追加
) -> List[SchemaAffiliateBroker]:
    """
    Retrieve a list of affiliate brokerage firms.

    Args:
        request: The FastAPI request object for rate limiting.
        db: The database session.
        region: Optional. Filter brokers by region (e.g., "US", "JP").
        active_only: If true, only return active brokers.
        limiter: The rate limiter instance.

    Returns:
        A list of AffiliateBroker schemas.
    """
    query = db.query(AffiliateBroker)
    if region:
        query = query.filter(AffiliateBroker.region == region)
    if active_only:
        query = query.filter(AffiliateBroker.is_active == True)

    brokers = query.all()

    # Convert 'pros' JSON string to list for each broker
    for broker in brokers:
        if broker.pros and isinstance(broker.pros, str):
            try:
                broker.pros = json.loads(broker.pros)
            except json.JSONDecodeError:
                broker.pros = [] # Default to empty list on error

    return brokers


@router.get(
    "/brokers/recommend",
    response_model=List[SchemaAffiliateBroker],
    summary="Get recommended affiliate brokers",
    description="Retrieve a list of recommended affiliate brokerage firms based on region, user level, and selected ETFs."
)
@limiter.limit("60/minute") # レート制限を追加
async def get_broker_recommendations(
    request: Request, # Requestを追加
    query_params: BrokerRecommendationQuery = Depends(),
    db: Session = Depends(get_db),
    limiter: Limiter = Depends(get_rate_limiter) # Limiterを追加
) -> List[SchemaAffiliateBroker]:
    """
    Retrieve a list of recommended affiliate brokerage firms.

    Args:
        request: The FastAPI request object for rate limiting.
        query_params: Query parameters including region, user level, and ETFs.
        db: The database session.
        limiter: The rate limiter instance.

    Returns:
        A list of recommended AffiliateBroker schemas, sorted by rating.
    """
    query = db.query(AffiliateBroker).filter(
        AffiliateBroker.region == query_params.region,
        AffiliateBroker.is_active == True
    )

    if query_params.user_level:
        # Simple matching for best_for. Could be more sophisticated.
        query = query.filter(
            or_(
                AffiliateBroker.best_for.ilike(f"%{query_params.user_level}%"),
                AffiliateBroker.best_for == "" # Also consider brokers not specifying a user_level
            )
        )
    
    # Further filtering by ETFs could be implemented here if broker-specific ETF lists were available
    # For now, it's a general recommendation based on user_level and region.

    brokers = query.order_by(AffiliateBroker.rating.desc()).limit(3).all()

    if not brokers:
        # Fallback to general brokers for the region if specific recommendation fails
        brokers = db.query(AffiliateBroker).filter(
            AffiliateBroker.region == query_params.region,
            AffiliateBroker.is_active == True
        ).order_by(AffiliateBroker.rating.desc()).limit(3).all()
        
        if not brokers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No brokers found for region: {query_params.region}"
            )

    # Convert 'pros' JSON string to list for each broker
    for broker in brokers:
        if broker.pros and isinstance(broker.pros, str):
            try:
                broker.pros = json.loads(broker.pros)
            except json.JSONDecodeError:
                broker.pros = []

    return brokers


@router.post(
    "/brokers/track-click",
    summary="Track an affiliate link click",
    description="Record details of a user clicking on an affiliate link for analytics and conversion tracking."
)
@limiter.limit("30/minute") # レート制限を追加
async def track_affiliate_click(
    request: Request, # Requestを追加
    click_data: TrackClickRequest,
    db: Session = Depends(get_db),
    # current_user_id: str = Depends(get_current_user_id) # Uncomment when user auth is integrated
    limiter: Limiter = Depends(get_rate_limiter) # Limiterを追加
) -> dict:
    """
    Record an affiliate link click.

    Args:
        request: The FastAPI request object for rate limiting.
        click_data: The data for the click event.
        db: The database session.
        # current_user_id: The ID of the authenticated user, if available.
        limiter: The rate limiter instance.

    Returns:
        A dictionary containing success status and redirect URL.
    """
    broker = db.query(AffiliateBroker).filter(
        AffiliateBroker.id == click_data.broker_id
    ).first()
    if not broker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Broker with ID {click_data.broker_id} not found."
        )

    # Placeholder for user_id - will be replaced with actual user ID from auth system
    user_id_from_auth: Optional[str] = None # get_current_user_id if available else None

    # Extract session_id, IP address, user agent, referrer
    # A robust session_id extraction would depend on how sessions are managed in the frontend/backend
    # For now, we'll use a simple approach or generate one if not provided.
    session_id = request.cookies.get("session_id") or request.headers.get("X-Session-ID") or "anonymous_session"
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    referrer = request.headers.get("Referer")

    new_click = AffiliateClick(
        broker_id=click_data.broker_id,
        user_id=user_id_from_auth,
        session_id=session_id,
        clicked_at=datetime.utcnow(),
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer,
        placement=click_data.placement,
        portfolio_data=json.dumps(click_data.portfolio_data) if click_data.portfolio_data else None,
        converted=False # Defaults to False on creation
    )

    db.add(new_click)
    db.commit()
    db.refresh(new_click)

    # Log the click event (optional, for separate analytics)
    print(f"Affiliate click tracked: Broker ID {new_click.broker_id}, Click ID {new_click.id}")

    return {
        "success": True,
        "click_id": new_click.id,
        "redirect_url": broker.affiliate_url
    }
