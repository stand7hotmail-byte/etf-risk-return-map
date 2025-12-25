from typing import Any, Dict

import numpy as np
from fastapi import APIRouter, Depends

from app.dependencies import get_simulation_service
from app.schemas import (
    DcaSimulationRequest,
    FutureDcaSimulationRequest,
    MonteCarloSimulationRequest,
)
from app.services.simulation_service import SimulationService

router = APIRouter(
    prefix="/simulation",
    tags=["Simulations"],
)


@router.post("/monte_carlo", response_model=Dict[str, Any])
async def run_monte_carlo(
    request: MonteCarloSimulationRequest,
    simulation_service: SimulationService = Depends(get_simulation_service),
) -> Dict[str, Any]:
    """
    Runs a Monte Carlo simulation for a portfolio with equal weights.
    
    Args:
        request: Simulation parameters including tickers, period, 
                 number of simulations, and simulation days
        
    Returns:
        Dictionary containing:
        - final_returns: List of final return values for each simulation
        - var_95: Value at Risk at 95% confidence level
        - cvar_95: Conditional Value at Risk at 95% confidence level
        
    Raises:
        HTTPException: 404 if tickers not found, 400 if parameters invalid
    """
    # Calculate equal weights for all tickers
    num_assets = len(request.tickers)
    weights = np.array([1.0 / num_assets] * num_assets) if num_assets > 0 else np.array([])

    return simulation_service.run_monte_carlo(
        tickers=request.tickers,
        weights=weights,
        period=request.period,
        num_simulations=request.num_simulations,
        simulation_days=request.simulation_days,
    )


@router.post("/historical_dca", response_model=Dict[str, Any])
async def run_historical_dca(
    request: DcaSimulationRequest,
    simulation_service: SimulationService = Depends(get_simulation_service),
) -> Dict[str, Any]:
    """
    Runs a historical Dollar-Cost Averaging (DCA) simulation.
    
    Args:
        request: DCA parameters including tickers, weights, investment amount,
                 frequency, and historical period
        
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
        tickers=request.tickers,
        weights=request.weights,
        investment_amount=request.investment_amount,
        frequency=request.frequency,
        period=request.period,
    )


@router.post("/future_dca", response_model=Dict[str, Any])
async def run_future_dca(
    request: FutureDcaSimulationRequest,
    simulation_service: SimulationService = Depends(get_simulation_service),
) -> Dict[str, Any]:
    """
    Runs a forward-looking, probabilistic DCA simulation based on portfolio metrics.
    
    Args:
        request: Future projection parameters including expected return/risk,
                 investment amount, frequency, and number of years
        
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
        portfolio_return=request.portfolio_return,
        portfolio_risk=request.portfolio_risk,
        investment_amount=request.investment_amount,
        frequency=request.frequency,
        years=request.years,
    )