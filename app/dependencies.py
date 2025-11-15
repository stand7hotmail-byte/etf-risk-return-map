from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from slowapi import Limiter
from sqlalchemy.orm import Session

from app.config import CACHE_TTL, ETF_DEFINITIONS, Settings, get_settings
from app.database import get_db
from app.models.portfolio import PortfolioCalculator
from app.services.data_service import DataService
from app.services.etf_service import ETFService
from app.services.optimization_service import OptimizationService
from app.services.simulation_service import SimulationService
from app.utils.cache import CacheManager


# --- Application Settings ---
def get_app_settings() -> Settings:
    """
    Returns the application settings as a dependency.
    Settings are cached by get_settings() internally.
    """
    return get_settings()


# --- Rate Limiter ---
def get_rate_limiter(request: Request) -> Limiter:
    """
    Returns the rate limiter instance from the application state.
    
    Args:
        request: The FastAPI request object.
    
    Returns:
        Limiter: The rate limiter instance.
    """
    return request.app.state.limiter


# --- Cache Manager (Singleton) ---
@lru_cache()
def get_cache_manager() -> CacheManager:
    """
    Provides a singleton CacheManager instance.
    Cached to ensure the same cache is used across all requests.
    
    Returns:
        CacheManager: The singleton cache manager instance.
    """
    return CacheManager(ttl=CACHE_TTL)


# --- Portfolio Calculator (Singleton) ---
@lru_cache()
def get_portfolio_calculator() -> PortfolioCalculator:
    """
    Provides a singleton PortfolioCalculator instance.
    The calculator is stateless and can be safely reused.
    
    Returns:
        PortfolioCalculator: The singleton calculator instance.
    """
    return PortfolioCalculator()


# --- Data Service (Per-request) ---
def get_data_service(
    db: Annotated[Session, Depends(get_db)],
    cache: Annotated[CacheManager, Depends(get_cache_manager)]
) -> DataService:
    """
    Provides a DataService instance for each request.
    
    Note: Not cached because db Session should be per-request.
    
    Args:
        db: Database session (per-request).
        cache: Shared cache manager instance.
    
    Returns:
        DataService: A new DataService instance.
    """
    return DataService(db=db, cache_manager=cache)


# --- ETF Service (Per-request) ---
def get_etf_service(
    data_service: Annotated[DataService, Depends(get_data_service)],
) -> ETFService:
    """
    Provides an ETFService instance for each request.
    
    Args:
        data_service: The data service instance.
    
    Returns:
        ETFService: A new ETFService instance.
    """
    return ETFService(
        etf_definitions=ETF_DEFINITIONS,
        data_service=data_service
    )


# --- Optimization Service (Per-request) ---
def get_optimization_service(
    calculator: Annotated[PortfolioCalculator, Depends(get_portfolio_calculator)],
    data_service: Annotated[DataService, Depends(get_data_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> OptimizationService:
    """
    Provides an OptimizationService instance for each request.
    
    Args:
        calculator: The portfolio calculator (singleton).
        data_service: The data service instance (per-request).
        settings: Application settings.
    
Returns:
        OptimizationService: A new OptimizationService instance.
    """
    return OptimizationService(
        calculator=calculator,
        data_service=data_service,
        risk_free_rate=settings.risk_free_rate,
    )


# --- Simulation Service (Per-request) ---
def get_simulation_service(
    data_service: Annotated[DataService, Depends(get_data_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> SimulationService:
    """
    Provides a SimulationService instance for each request.
    
    Args:
        data_service: The data service instance.
        settings: Application settings.
    
    Returns:
        SimulationService: A new SimulationService instance.
    """
    return SimulationService(
        data_service=data_service,
        risk_free_rate=settings.risk_free_rate
    )


# --- Type Aliases for convenience ---
DBSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
CacheManagerDep = Annotated[CacheManager, Depends(get_cache_manager)]
PortfolioCalculatorDep = Annotated[PortfolioCalculator, Depends(get_portfolio_calculator)]
DataServiceDep = Annotated[DataService, Depends(get_data_service)]
ETFServiceDep = Annotated[ETFService, Depends(get_etf_service)]
OptimizationServiceDep = Annotated[OptimizationService, Depends(get_optimization_service)]
SimulationServiceDep = Annotated[SimulationService, Depends(get_simulation_service)]