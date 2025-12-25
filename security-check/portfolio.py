from typing import List

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_optimization_service
from app.schemas import (
    CustomPortfolioRequest,
    TargetOptimizationRequest,
    OptimizationResult,
    PortfolioMetrics,
)
from app.services.optimization_service import OptimizationService

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio Optimization"],
)


@router.get("/efficient_frontier", response_model=OptimizationResult)
async def get_efficient_frontier(
    tickers: List[str] = Query(..., description="List of tickers for analysis"),
    period: str = Query("5y", description="Period for historical data (e.g., '5y')"),
    optimization_service: OptimizationService = Depends(get_optimization_service),
) -> OptimizationResult:
    """
    Calculates the efficient frontier and tangency portfolio for a given set of ETFs.
    
    Args:
        tickers: List of ETF ticker symbols to analyze
        period: Historical data period (e.g., "1y", "5y", "10y")
        
    Returns:
        OptimizationResult containing:
        - etf_data: Individual ETF risk/return metrics
        - frontier_points: Points on the efficient frontier
        - tangency_portfolio: Maximum Sharpe ratio portfolio
        - tangency_portfolio_weights: Optimal asset allocation
        
    Raises:
        HTTPException: 404 if tickers not found, 400 if calculation fails
    """
    return optimization_service.calculate_efficient_frontier(tickers, period)


@router.post("/custom_metrics", response_model=PortfolioMetrics)
async def get_custom_portfolio_metrics(
    request: CustomPortfolioRequest,
    optimization_service: OptimizationService = Depends(get_optimization_service),
) -> PortfolioMetrics:
    """
    Calculates risk and return for a custom portfolio with specific weights.
    
    Args:
        request: Portfolio specification including tickers, weights, and period
        
    Returns:
        PortfolioMetrics containing risk and return values
        
    Raises:
        HTTPException: 404 if tickers not found, 400 if weights invalid
    """
    return optimization_service.calculate_custom_portfolio_metrics(
        request.tickers, request.weights, request.period
    )


@router.post("/optimize_by_return", response_model=PortfolioMetrics)
async def optimize_by_return(
    request: TargetOptimizationRequest,
    optimization_service: OptimizationService = Depends(get_optimization_service),
) -> PortfolioMetrics:
    """
    Optimizes a portfolio to achieve a target return while minimizing risk.
    
    Args:
        request: Target return specification and tickers
        
    Returns:
        PortfolioMetrics with optimized weights and resulting risk/return
        
    Raises:
        HTTPException: 404 if tickers not found, 400 if target unachievable
    """
    return optimization_service.optimize_by_target_return(
        request.tickers, request.target_value, request.period
    )


@router.post("/optimize_by_risk", response_model=PortfolioMetrics)
async def optimize_by_risk(
    request: TargetOptimizationRequest,
    optimization_service: OptimizationService = Depends(get_optimization_service),
) -> PortfolioMetrics:
    """
    Optimizes a portfolio to match a target risk level while maximizing return.
    
    Args:
        request: Target risk specification and tickers
        
    Returns:
        PortfolioMetrics with optimized weights and resulting risk/return
        
    Raises:
        HTTPException: 404 if tickers not found, 400 if target unachievable
    """
    return optimization_service.optimize_by_target_risk(
        request.tickers, request.target_value, request.period
    )