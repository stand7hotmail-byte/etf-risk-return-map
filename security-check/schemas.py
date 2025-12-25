from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for user creation."""

    username: str = Field(..., max_length=50)
    password: str = Field(..., max_length=128)


class UserInDB(BaseModel):
    """Schema for user data stored in the database."""

    username: str
    hashed_password: str


class Token(BaseModel):
    """Schema for OAuth2 token."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token payload data."""

    username: str | None = None


class GoogleToken(BaseModel):
    """Schema for Google OAuth2 token."""

    token: str


class CustomPortfolioRequest(BaseModel):
    """Schema for custom portfolio calculation requests."""

    tickers: list[str]
    weights: dict[str, float]
    period: str = "5y"


class TargetOptimizationRequest(BaseModel):
    """Schema for target optimization requests."""

    tickers: list[str]
    target_value: float
    period: str = "5y"


class HistoricalPerformanceRequest(BaseModel):
    """Schema for historical performance requests."""

    tickers: list[str]
    period: str = "5y"


class MonteCarloSimulationRequest(BaseModel):
    """Schema for Monte Carlo simulation requests."""

    tickers: list[str]
    period: str = "5y"
    num_simulations: int
    simulation_days: int


class CSVAnalysisRequest(BaseModel):
    """Schema for CSV analysis requests."""

    csv_data: str


class DcaSimulationRequest(BaseModel):
    """Schema for DCA simulation requests."""

    tickers: list[str]
    weights: dict[str, float]
    period: str = "5y"
    investment_amount: float
    frequency: str  # 'monthly' or 'quarterly'


class FutureDcaSimulationRequest(BaseModel):
    """Schema for future DCA simulation requests."""

    portfolio_return: float
    portfolio_risk: float
    investment_amount: float
    frequency: str
    years: int


class ETFData(BaseModel):
    """Schema for individual ETF data."""
    Ticker: str
    Return: float
    Risk: float


class EfficientFrontierPoint(BaseModel):
    """Schema for a point on the efficient frontier."""
    Return: float
    Risk: float


class TangencyPortfolio(BaseModel):
    """Schema for tangency portfolio details."""
    Return: float
    Risk: float
    SharpeRatio: float


class OptimizationResult(BaseModel):
    """Schema for the result of efficient frontier calculation."""
    etf_data: list[ETFData]
    frontier_points: list[EfficientFrontierPoint]
    tangency_portfolio: TangencyPortfolio | None
    tangency_portfolio_weights: dict[str, float]


class PortfolioMetrics(BaseModel):
    """Schema for portfolio metrics."""
    Risk: float
    Return: float
    SortinoRatio: float | None = None
    weights: dict[str, float] | None = None
    details: str | None = None
    error: str | None = None


# --- Affiliate Schemas ---
class AffiliateBrokerBase(BaseModel):
    """Base schema for affiliate broker data."""
    broker_name: str = Field(..., max_length=100, examples=["interactive_brokers"])
    display_name: str = Field(..., max_length=100, examples=["Interactive Brokers"])
    region: str = Field(..., max_length=10, examples=["US"])
    affiliate_url: str = Field(..., examples=["https://ibkr.com/referral/placeholder"])
    commission_rate: float = Field(..., ge=0, examples=[200.0])
    commission_type: str = Field(..., max_length=20, examples=["CPA"])
    logo_url: Optional[str] = Field(None, max_length=255, examples=["/static/images/brokers/ibkr.png"])
    description: str = Field(..., examples=["グローバル対応の総合証券会社。11,000以上のETFを手数料無料で取引可能。"])
    pros: List[str] = Field(..., examples=["[\"低コスト\", \"グローバル対応\"]"])
    best_for: str = Field(..., max_length=255, examples=["中級〜上級投資家"])
    rating: float = Field(..., ge=1, le=5, examples=[4.5])
    is_active: bool = Field(True)

class AffiliateBrokerCreate(AffiliateBrokerBase):
    """Schema for creating a new affiliate broker."""
    pass

class AffiliateBroker(AffiliateBrokerBase):
    """Schema for retrieving an affiliate broker from the database."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Allow ORM models to be converted to Pydantic models


class AffiliateClickCreate(BaseModel):
    """Schema for creating a new affiliate click record."""
    broker_id: int
    placement: str = Field(..., max_length=100, examples=["portfolio_result"])
    user_id: Optional[str] = Field(None, max_length=100)
    session_id: str = Field(..., max_length=255)
    ip_address: Optional[str] = Field(None, max_length=50)
    user_agent: Optional[str] = Field(None)
    referrer: Optional[str] = Field(None)
    portfolio_data: Optional[str] = Field(None) # Stored as JSON string


class AffiliateClick(AffiliateClickCreate):
    """Schema for retrieving an affiliate click from the database."""
    id: int
    clicked_at: datetime
    converted: bool
    converted_at: Optional[datetime]

    class Config:
        from_attributes = True


class BrokerRecommendationQuery(BaseModel):
    """Query parameters for broker recommendations."""
    region: str = Field(..., examples=["US", "JP"])
    user_level: Optional[str] = Field(None, examples=["beginner", "intermediate"])
    etfs: Optional[List[str]] = Field(None, examples=[["VTI", "BND"]])

class TrackClickRequest(BaseModel):
    """Request body for tracking an affiliate click."""
    broker_id: int
    placement: str = Field(..., max_length=100, examples=["portfolio_result"])
    portfolio_data: Optional[dict] = Field(None) # Pydantic will handle dict to JSON string conversion


# --- Admin Affiliate Schemas ---
class AffiliatePeriodStats(BaseModel):
    """Schema for affiliate statistics within a period."""
    start: datetime
    end: datetime

class BrokerPerformanceStats(BaseModel):
    """Schema for a single broker's performance stats."""
    broker_name: str
    clicks: int
    conversions: int
    conversion_rate: float
    revenue: float

class PlacementPerformanceStats(BaseModel):
    """Schema for a single placement's performance stats."""
    placement: str
    clicks: int
    conversions: int
    conversion_rate: float

class DailyPerformanceStats(BaseModel):
    """Schema for daily performance statistics."""
    date: str
    clicks: int
    conversions: int

class AffiliateStatsResponse(BaseModel):
    """Schema for overall affiliate statistics response."""
    period: AffiliatePeriodStats
    total_clicks: int
    total_conversions: int
    conversion_rate: float
    estimated_revenue: float
    by_broker: List[BrokerPerformanceStats]
    by_placement: List[PlacementPerformanceStats]
    daily_performance: List[DailyPerformanceStats]

class TopPerformingBroker(BaseModel):
    """Schema for a top performing broker."""
    broker_id: int
    broker_name: str
    display_name: str
    clicks: int
    conversions: int
    conversion_rate: float
    revenue: float

class ManualConversionRequest(BaseModel):
    """Schema for manually recording a conversion."""
    click_id: int
    converted_at: Optional[datetime] = Field(None, description="Defaults to now if not provided.")