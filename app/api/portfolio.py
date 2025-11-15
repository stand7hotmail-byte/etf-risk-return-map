from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_optimization_service
from app.schemas import CustomPortfolioRequest, TargetOptimizationRequest
from app.services.optimization_service import OptimizationService

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio Optimization"],
)

# In the original code, the default tickers were loaded from the CSV.
# For now, we'll make the query required. This can be adjusted.
# ALL_ETF_TICKERS = [] # This would be loaded from config if needed

@router.get("/efficient_frontier", response_model=Dict[str, Any])
async def get_efficient_frontier(
    tickers: List[str] = Query(..., description="List of tickers for analysis"),
    period: str = Query("5y", description="Period for historical data (e.g., '5y')"),
    optimization_service: OptimizationService = Depends(get_optimization_service),
):
    """
    Calculates the efficient frontier and tangency portfolio for a given set of ETFs.
    """
    return optimization_service.calculate_efficient_frontier(tickers, period)


@router.post("/custom_metrics", response_model=Dict[str, Any])
async def get_custom_portfolio_metrics(
    request: CustomPortfolioRequest,
    optimization_service: OptimizationService = Depends(get_optimization_service),
):
    """
    Calculates risk and return for a custom portfolio with specific weights.
    """
    return optimization_service.calculate_custom_portfolio_metrics(
        request.tickers, request.weights, request.period
    )


@router.post("/optimize_by_return", response_model=Dict[str, Any])
async def optimize_by_return(
    request: TargetOptimizationRequest,
    optimization_service: OptimizationService = Depends(get_optimization_service),
):
    """
    Optimizes a portfolio to achieve a target return while minimizing risk.
    """
    return optimization_service.optimize_by_target_return(
        request.tickers, request.target_value, request.period
    )


@router.post("/optimize_by_risk", response_model=Dict[str, Any])
async def optimize_by_risk(
    request: TargetOptimizationRequest,
    optimization_service: OptimizationService = Depends(get_optimization_service),
):
    """
    Optimizes a portfolio to match a target risk level while maximizing return.
    """
    return optimization_service.optimize_by_target_risk(
        request.tickers, request.target_value, request.period
    )
