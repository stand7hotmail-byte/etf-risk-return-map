from typing import List

from fastapi import APIRouter, Depends, Query, Request # Requestを追加
from slowapi import Limiter # 追加

from app.dependencies import get_optimization_service, get_rate_limiter # get_rate_limiterを追加
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
@limiter.limit("30/minute") # レート制限を追加
async def get_efficient_frontier(
    request: Request, # Requestを追加
    tickers: List[str] = Query(..., description="List of tickers for analysis"),
    period: str = Query("5y", description="Period for historical data (e.g., '5y')"),
    optimization_service: OptimizationService = Depends(get_optimization_service),
    limiter: Limiter = Depends(get_rate_limiter) # Limiterを追加
) -> OptimizationResult:
    """
    Calculates the efficient frontier and tangency portfolio for a given set of ETFs.
    
    Args:
        request: The FastAPI request object for rate limiting.
        tickers: List of ETF ticker symbols to analyze
        period: Historical data period (e.g., "1y", "5y", "10y")
        optimization_service: The optimization service instance.
        limiter: The rate limiter instance.
        
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
@limiter.limit("30/minute") # レート制限を追加
async def get_custom_portfolio_metrics(
    request: Request, # Requestを追加
    custom_portfolio_request: CustomPortfolioRequest, # requestからcustom_portfolio_requestに名前変更
    optimization_service: OptimizationService = Depends(get_optimization_service),
    limiter: Limiter = Depends(get_rate_limiter) # Limiterを追加
) -> PortfolioMetrics:
    """
    Calculates risk and return for a custom portfolio with specific weights.
    
    Args:
        request: The FastAPI request object for rate limiting.
        custom_portfolio_request: Portfolio specification including tickers, weights, and period.
        optimization_service: The optimization service instance.
        limiter: The rate limiter instance.
        
    Returns:
        PortfolioMetrics containing risk and return values
        
    Raises:
        HTTPException: 404 if tickers not found, 400 if weights invalid
    """
    return optimization_service.calculate_custom_portfolio_metrics(
        custom_portfolio_request.tickers, custom_portfolio_request.weights, custom_portfolio_request.period
    )


@router.post("/optimize_by_return", response_model=PortfolioMetrics)
@limiter.limit("30/minute") # レート制限を追加
async def optimize_by_return(
    request: Request, # Requestを追加
    target_optimization_request: TargetOptimizationRequest, # requestからtarget_optimization_requestに名前変更
    optimization_service: OptimizationService = Depends(get_optimization_service),
    limiter: Limiter = Depends(get_rate_limiter) # Limiterを追加
) -> PortfolioMetrics:
    """
    Optimizes a portfolio to achieve a target return while minimizing risk.
    
    Args:
        request: The FastAPI request object for rate limiting.
        target_optimization_request: Target return specification and tickers.
        optimization_service: The optimization service instance.
        limiter: The rate limiter instance.
        
    Returns:
        PortfolioMetrics with optimized weights and resulting risk/return
        
    Raises:
        HTTPException: 404 if tickers not found, 400 if target unachievable
    """
    return optimization_service.optimize_by_target_return(
        target_optimization_request.tickers, target_optimization_request.target_value, target_optimization_request.period
    )


@router.post("/optimize_by_risk", response_model=PortfolioMetrics)
@limiter.limit("30/minute") # レート制限を追加
async def optimize_by_risk(
    request: Request, # Requestを追加
    target_optimization_request: TargetOptimizationRequest, # requestからtarget_optimization_requestに名前変更
    optimization_service: OptimizationService = Depends(get_optimization_service),
    limiter: Limiter = Depends(get_rate_limiter) # Limiterを追加
) -> PortfolioMetrics:
    """
    Optimizes a portfolio to match a target risk level while maximizing return.
    
    Args:
        request: The FastAPI request object for rate limiting.
        target_optimization_request: Target risk specification and tickers.
        optimization_service: The optimization service instance.
        limiter: The rate limiter instance.
        
    Returns:
        PortfolioMetrics with optimized weights and resulting risk/return
        
    Raises:
        HTTPException: 404 if tickers not found, 400 if target unachievable
    """
    return optimization_service.optimize_by_target_risk(
        target_optimization_request.tickers, target_optimization_request.target_value, target_optimization_request.period
    )