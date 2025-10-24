
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., max_length=128)


class UserInDB(BaseModel):
    username: str
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class GoogleToken(BaseModel):
    token: str


class CustomPortfolioRequest(BaseModel):
    tickers: list[str]
    weights: dict[str, float]
    period: str = "5y"


class TargetOptimizationRequest(BaseModel):
    tickers: list[str]
    target_value: float
    period: str = "5y"


class HistoricalPerformanceRequest(BaseModel):
    tickers: list[str]
    period: str = "5y"


class MonteCarloSimulationRequest(BaseModel):
    tickers: list[str]
    period: str = "5y"
    num_simulations: int
    simulation_days: int


class CSVAnalysisRequest(BaseModel):
    csv_data: str


class DcaSimulationRequest(BaseModel):
    tickers: list[str]
    weights: dict[str, float]
    period: str = "5y"
    investment_amount: float
    frequency: str  # 'monthly' or 'quarterly'


class FutureDcaSimulationRequest(BaseModel):
    portfolio_return: float
    portfolio_risk: float
    investment_amount: float
    frequency: str
    years: int
