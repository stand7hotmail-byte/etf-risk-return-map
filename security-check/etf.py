from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.dependencies import get_app_settings, get_etf_service
from app.config import Settings
from app.services.etf_service import ETFService

router = APIRouter(
    prefix="/etfs",
    tags=["ETFs"],
)


@router.get("/list", response_model=Dict[str, Any])
async def get_etf_list(
    etf_service: ETFService = Depends(get_etf_service),
) -> Dict[str, Any]:
    """
    Returns a dictionary of all available ETF definitions from the static CSV file.
    
    Returns:
        Dictionary mapping ticker symbols to their metadata including:
        - asset_class: Type of asset (e.g., Equity, Bond)
        - region: Geographic region
        - name: Full ETF name
        - style: Investment style
        - size: Market cap size
        - sector: Industry sector
        - theme: Investment theme
        
    Raises:
        HTTPException: 500 if ETF definitions file cannot be loaded
    """
    return etf_service.get_all_etfs()


@router.get("/details/{ticker}", response_model=Dict[str, Any])
async def get_etf_details(
    ticker: str,
    etf_service: ETFService = Depends(get_etf_service),
) -> Dict[str, Any]:
    """
    Retrieves detailed information for a given ETF ticker, combining static
    data with live data from yfinance.
    
    Args:
        ticker: ETF ticker symbol (e.g., "VTI", "BND")
        
    Returns:
        Dictionary containing:
        - basicInfo: Name, fund family, and generated summary
        - keyMetrics: AUM, yield, expense ratio, YTD return, beta, 52-week range
        
    Raises:
        HTTPException: 404 if ticker not found, 503 if yfinance unavailable
    """
    return etf_service.get_etf_details(ticker)


@router.get("/risk_free_rate", response_model=Dict[str, float])
async def get_risk_free_rate(
    settings: Settings = Depends(get_app_settings),
) -> Dict[str, float]:
    """
    Returns the application-wide risk-free rate used in calculations.
    
    Returns:
        Dictionary containing the risk-free rate value
        
    Note:
        This rate is used for Sharpe ratio and Sortino ratio calculations
    """
    return {"risk_free_rate": settings.risk_free_rate}