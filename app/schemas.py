from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator
import re


class UserCreate(BaseModel):
    """Schema for user creation."""

    username: str = Field(
        min_length=3,
        max_length=50,
        description="Username must be 3-50 characters"
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters"
    )
    
    @validator('username')
    def validate_username(cls, v):
        """ユーザー名は英数字とアンダースコアのみ"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """パスワードの複雑性チェック"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v


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
    broker_name: str = Field(
        min_length=1,
        max_length=100,
        description="Unique broker identifier",
        examples=["interactive_brokers"]
    )
    display_name: str = Field(
        min_length=1,
        max_length=200,
        description="Display name",
        examples=["Interactive Brokers"]
    )
    region: str = Field(
        max_length=10,
        description="Region code",
        examples=["US"]
    )
    affiliate_url: str = Field(
        max_length=500,
        description="Affiliate URL",
        examples=["https://ibkr.com/referral/placeholder"]
    )
    commission_rate: float = Field(
        ge=0,
        description="Commission rate (must be non-negative)",
        examples=[200.0]
    )
    commission_type: str = Field(
        max_length=20,
        description="Commission type",
        examples=["CPA"]
    )
    logo_url: Optional[str] = Field(None, max_length=255, examples=["/static/images/brokers/ibkr.png"])
    description: str = Field(
        max_length=1000,
        description="Broker description",
        examples=["グローバル対応の総合証券会社。11,000以上のETFを手数料無料で取引可能。"]
    )
    pros: str = Field(
        description="JSON string of pros",
        examples=["[\"低コスト\", \"グローバル対応\"]"]
    )  # JSON文字列として保存されている場合
    best_for: str = Field(
        max_length=200,
        description="Best for target audience",
        examples=["中級〜上級投資家"]
    )
    rating: float = Field(
        ge=0,
        le=5,
        description="Rating from 0 to 5",
        examples=[4.5]
    )
    is_active: bool = Field(True)

    @validator('region')
    def validate_region(cls, v):
        """地域コードは許可された値のみ"""
        allowed_regions = ['US', 'JP', 'EU', 'Global', 'Global ex-US', 'Developed ex-US', 'Emerging']
        if v not in allowed_regions:
            raise ValueError(f'Region must be one of: {", ".join(allowed_regions)}')
        return v
    
    @validator('commission_type')
    def validate_commission_type(cls, v):
        """報酬タイプは許可された値のみ"""
        allowed_types = ['CPA', 'RevShare', 'Hybrid', 'CPM'] # CPMを追加
        if v not in allowed_types:
            raise ValueError(f'Commission type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('pros')
    def validate_pros(cls, v):
        """prosがJSON形式の文字列か確認"""
        import json
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, list):
                raise ValueError('pros must be a JSON array')
            if not all(isinstance(item, str) for item in parsed):
                raise ValueError('pros array must contain only strings')
        except json.JSONDecodeError:
            raise ValueError('pros must be valid JSON')
        return v

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
    broker_id: int = Field(
        gt=0,
        description="Broker ID must be a positive integer"
    )
    placement: str = Field(
        max_length=50,
        description="Placement location"
    )
    portfolio_data: Optional[dict] = Field(
        default=None,
        description="Portfolio data (optional)"
    ) # Pydantic will handle dict to JSON string conversion

    @validator('placement')
    def validate_placement(cls, v):
        """配置場所は許可された値のみ"""
        allowed_placements = [
            'portfolio_result',
            'broker_page',
            'blog_post',
            'comparison_page'
        ]
        if v not in allowed_placements:
            raise ValueError(f'Placement must be one of: {", ".join(allowed_placements)}')
        return v
    
    @validator('portfolio_data')
    def validate_portfolio_data(cls, v):
        """ポートフォリオデータの構造検証"""
        if v is None:
            return v
        
        # tickers と weights が含まれているか確認
        if 'tickers' in v:
            if not isinstance(v['tickers'], list):
                raise ValueError('portfolio_data.tickers must be a list')
            if not all(isinstance(t, str) for t in v['tickers']):
                raise ValueError('portfolio_data.tickers must contain only strings')
        
        if 'weights' in v:
            if not isinstance(v['weights'], dict):
                raise ValueError('portfolio_data.weights must be a dict')
        
        return v


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