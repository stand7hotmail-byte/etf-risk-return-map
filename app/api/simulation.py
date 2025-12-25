from typing import Any, Dict

import numpy as np
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter # 追加
from slowapi.util import get_remote_address # 追加

from app.dependencies import get_simulation_service # get_rate_limiterは不要になる
from app.schemas import (
    DcaSimulationRequest,
    FutureDcaSimulationRequest,
    MonteCarloSimulationRequest,
)
from app.services.simulation_service import SimulationService

# 各ルーターファイルで個別のLimiterインスタンスを定義
# このlimiterがデコレータで参照される
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/simulation",
    tags=["Simulations"],
)


@router.post("/monte_carlo", response_model=Dict[str, Any])
@limiter.limit("10/minute") # レート制限を追加
async def run_monte_carlo(
    request: Request, # Requestを追加
    monte_carlo_request: MonteCarloSimulationRequest, # requestからmonte_carlo_requestに名前変更
    simulation_service: SimulationService = Depends(get_simulation_service),
    # limiter: Limiter = Depends(get_rate_limiter) # ここは不要になる
) -> Dict[str, Any]:
    """
    Runs a Monte Carlo simulation for a portfolio with equal weights.
    
    Args:
        request: The FastAPI request object for rate limiting.
        monte_carlo_request: Simulation parameters including tickers, period, 
                 number of simulations, and simulation days.
        simulation_service: The simulation service instance.
        # limiter: The rate limiter instance. # ここは不要になる
        
    Returns:
        Dictionary containing:
        - final_returns: List of final return values for each simulation
        - var_95: Value at Risk at 95% confidence level
        - cvar_95: Conditional Value at Risk at 95% confidence level
        
    Raises:
        HTTPException: 404 if tickers not found, 400 if parameters invalid
    """
    # Calculate equal weights for all tickers
    num_assets = len(monte_carlo_request.tickers)
    weights = np.array([1.0 / num_assets] * num_assets) if num_assets > 0 else np.array([])

    return simulation_service.run_monte_carlo(
        tickers=monte_carlo_request.tickers,
        weights=weights,
        period=monte_carlo_request.period,
        num_simulations=monte_carlo_request.num_simulations,
        simulation_days=monte_carlo_request.simulation_days,
    )


@router.post("/historical_dca", response_model=Dict[str, Any])
@limiter.limit("20/minute") # レート制限を追加
async def run_historical_dca(
    request: Request, # Requestを追加
    dca_simulation_request: DcaSimulationRequest, # requestからdca_simulation_requestに名前変更
    simulation_service: SimulationService = Depends(get_simulation_service),
    # limiter: Limiter = Depends(get_rate_limiter) # ここは不要になる
) -> Dict[str, Any]:
    """
    Runs a historical Dollar-Cost Averaging (DCA) simulation.
    
    Args:
        request: The FastAPI request object for rate limiting.
        dca_simulation_request: DCA parameters including tickers, weights, investment amount,
                 frequency, and historical period.
        simulation_service: The simulation service instance.
        # limiter: The rate limiter instance. # ここは不要になる
        
    Returns:
        Dictionary containing:
        - dates: List of dates for the simulation
        - portfolio_values: Portfolio value at each date
        - total_invested: Total amount invested
        - final_value: Final portfolio value
        - profit_loss: Net profit or loss
        
    Raises:
        HTTPException: 404 if tickers not found, 400 if parameters invalid
    """
    return simulation_service.run_historical_dca(
        tickers=dca_simulation_request.tickers,
        weights=dca_simulation_request.weights,
        investment_amount=dca_simulation_request.investment_amount,
        frequency=dca_simulation_request.frequency,
        period=dca_simulation_request.period,
    )


@router.post("/future_dca", response_model=Dict[str, Any])
@limiter.limit("20/minute") # レート制限を追加
async def run_future_dca(
    request: Request, # Requestを追加
    future_dca_simulation_request: FutureDcaSimulationRequest, # requestからfuture_dca_simulation_requestに名前変更
    simulation_service: SimulationService = Depends(get_simulation_service),
    # limiter: Limiter = Depends(get_rate_limiter) # ここは不要になる
) -> Dict[str, Any]:
    """
    Runs a forward-looking, probabilistic DCA simulation based on portfolio metrics.
    
    Args:
        request: The FastAPI request object for rate limiting.
        future_dca_simulation_request: Future projection parameters including expected return/risk,
                 investment amount, frequency, and number of years.
        simulation_service: The simulation service instance.
        # limiter: The rate limiter instance. # ここは不要になる
        
    Returns:
        Dictionary containing:
        - time_labels: Time period labels
        - mean_scenario: Mean portfolio value trajectory
        - upper_scenario: 95th percentile scenario
        - lower_scenario: 5th percentile scenario
        - total_invested: Cumulative investment over time
        - final_mean_value: Expected final portfolio value
        
    Raises:
        HTTPException: 400 if parameters invalid
    """
    return simulation_service.run_future_dca(
        portfolio_return=future_dca_simulation_request.portfolio_return,
        portfolio_risk=future_dca_simulation_request.portfolio_risk,
        investment_amount=future_dca_simulation_request.investment_amount,
        frequency=future_dca_simulation_request.frequency,
        years=future_dca_simulation_request.years,
    )