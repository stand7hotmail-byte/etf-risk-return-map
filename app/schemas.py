
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
