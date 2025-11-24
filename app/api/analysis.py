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
) -> Dict[str, Any]:
    """
    Retrieves historical performance (cumulative returns) for a list of tickers.
    
    Args:
        request: Historical performance request with tickers and period
        
    Returns:
        Dictionary containing:
        - dates: List of dates
        - cumulative_returns: Dict mapping tickers to their cumulative return series
        
    Raises:
        HTTPException: 404 if tickers not found, 400 if period invalid
    """
    return data_service.get_historical_performance(request.tickers, request.period)


@router.post("/correlation_matrix", response_model=Dict[str, Any])
async def get_correlation_matrix(
    request: HistoricalPerformanceRequest,
    data_service: DataService = Depends(get_data_service),
) -> Dict[str, Any]:
    """
    Calculates the correlation matrix for a list of tickers.
    
    Args:
        request: Correlation matrix request with tickers and period
        
    Returns:
        Dictionary formatted for heatmap visualization:
        - x: List of ticker symbols (columns)
        - y: List of ticker symbols (rows)
        - z: 2D array of correlation values
        
    Raises:
        HTTPException: 404 if tickers not found, 400 if insufficient data
    """
    return data_service.get_correlation_matrix(request.tickers, request.period)


@router.post("/csv", response_model=List[Dict[str, Any]])
async def analyze_csv_data(
    request: CSVAnalysisRequest,
    data_service: DataService = Depends(get_data_service),
) -> List[Dict[str, Any]]:
    """
    Analyzes ETF data from a provided CSV file string and returns risk/return metrics.
    
    Args:
        request: CSV analysis request containing CSV data as string
        
    Returns:
        List of dictionaries, each containing:
        - Ticker: ETF ticker symbol
        - Risk: Annualized volatility
        - Return: Annualized return
        
    Raises:
        HTTPException: 400 if CSV format invalid or data insufficient
    """
    return data_service.load_and_analyze_csv(request.csv_data)