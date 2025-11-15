from datetime import timedelta
from functools import lru_cache

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


def get_rate_limiter(request: Request) -> Limiter:
    """Returns the rate limiter instance from the application state."""
    return request.app.state.limiter


def get_app_settings() -> Settings:
    """Returns the application settings as a dependency."""
    return get_settings()


@lru_cache()
def get_cache_manager() -> CacheManager:
    """Provides a singleton CacheManager instance."""
    return CacheManager(ttl=CACHE_TTL)


@lru_cache()
def get_portfolio_calculator() -> PortfolioCalculator:
    """Provides a singleton PortfolioCalculator instance."""
    return PortfolioCalculator()


@lru_cache()
def get_data_service(
    db: Session = Depends(get_db), cache: CacheManager = Depends(get_cache_manager)
) -> DataService:
    """Provides a singleton DataService instance."""
    return DataService(db=db, cache_manager=cache)


@lru_cache()
def get_etf_service(
    data_service: DataService = Depends(get_data_service),
) -> ETFService:
    """Provides a singleton ETFService instance."""
    return ETFService(etf_definitions=ETF_DEFINITIONS, data_service=data_service)


@lru_cache()
def get_optimization_service(
    calculator: PortfolioCalculator = Depends(get_portfolio_calculator),
    data_service: DataService = Depends(get_data_service),
    settings: Settings = Depends(get_app_settings),
) -> OptimizationService:
    """Provides a singleton OptimizationService instance."""
    return OptimizationService(
        calculator=calculator,
        data_service=data_service,
        risk_free_rate=settings.risk_free_rate,
    )


@lru_cache()
def get_simulation_service(
    data_service: DataService = Depends(get_data_service),
) -> SimulationService:
    """Provides a singleton SimulationService instance."""
    return SimulationService(data_service=data_service)
