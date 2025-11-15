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
):
    """
    Runs a Monte Carlo simulation for a portfolio with equal weights.
    """
    # The original endpoint assumed equal weights. We'll do the same here.
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
):
    """
    Runs a historical Dollar-Cost Averaging (DCA) simulation.
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
):
    """
    Runs a forward-looking, probabilistic DCA simulation based on portfolio metrics.
    """
    return simulation_service.run_future_dca(
        portfolio_return=request.portfolio_return,
        portfolio_risk=request.portfolio_risk,
        investment_amount=request.investment_amount,
        frequency=request.frequency,
        years=request.years,
    )
