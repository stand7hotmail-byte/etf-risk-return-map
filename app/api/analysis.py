from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.dependencies import get_data_service
from app.schemas import CSVAnalysisRequest, HistoricalPerformanceRequest
from app.services.data_service import DataService

router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)


@router.post("/historical_performance", response_model=Dict[str, Any])
async def get_historical_performance(
    request: HistoricalPerformanceRequest,
    data_service: DataService = Depends(get_data_service),
):
    """
    Retrieves historical performance (cumulative returns) for a list of tickers.
    """
    return data_service.get_historical_performance(request.tickers, request.period)


@router.post("/correlation_matrix", response_model=Dict[str, Any])
async def get_correlation_matrix(
    request: HistoricalPerformanceRequest,
    data_service: DataService = Depends(get_data_service),
):
    """
    Calculates the correlation matrix for a list of tickers.
    """
    return data_service.get_correlation_matrix(request.tickers, request.period)


@router.post("/csv", response_model=List[Dict[str, Any]])
async def analyze_csv_data(
    request: CSVAnalysisRequest,
    data_service: DataService = Depends(get_data_service),
):
    """
    Analyzes ETF data from a provided CSV file string and returns risk/return metrics.
    """
    return data_service.load_and_analyze_csv(request.csv_data)
