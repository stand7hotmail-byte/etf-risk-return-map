from typing import Any, Dict

from fastapi import APIRouter, Depends
from app.config import Settings

from app.dependencies import get_app_settings, get_etf_service
from app.services.etf_service import ETFService

router = APIRouter(
    prefix="/etfs",
    tags=["ETFs"],
)


@router.get("/list", response_model=Dict[str, Any])
async def get_etf_list(
    etf_service: ETFService = Depends(get_etf_service),
):
    """
    Returns a dictionary of all available ETF definitions from the static CSV file.
    """
    return etf_service.get_all_etfs()


@router.get("/details/{ticker}", response_model=Dict[str, Any])
async def get_etf_details(
    ticker: str,
    etf_service: ETFService = Depends(get_etf_service),
):
    """
    Retrieves detailed information for a given ETF ticker, combining static
    data with live data from yfinance.
    """
    return etf_service.get_etf_details(ticker)


@router.get("/risk_free_rate", response_model=Dict[str, float])
async def get_risk_free_rate(
    settings: Settings = Depends(get_app_settings),
):
    """
    Returns the application-wide risk-free rate.
    """
    return {"risk_free_rate": settings.risk_free_rate}
