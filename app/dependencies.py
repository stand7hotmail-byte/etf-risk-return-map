import os
from functools import lru_cache
from typing import Annotated, Generator
from datetime import datetime, timedelta

from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer
from slowapi import Limiter # Limiterをインポート
# from fastapi.security.oauth2 import HTTPAuthorizationCredentials # 修正: この行は不要になる
from jose import JWTError, jwt

from sqlalchemy.orm import Session

from app.config import CACHE_TTL, ETF_DEFINITIONS, Settings, get_settings
from app.database import get_db
from app.models.portfolio import PortfolioCalculator
from app.services.data_service import DataService
from app.services.etf_service import ETFService
from app.services.optimization_service import OptimizationService
from app.services.simulation_service import SimulationService
from app.utils.cache import CacheManager


# --- JWT Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    JWTアクセス_トークンを作成
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # is_admin フラグを含める
    to_encode.update({"is_admin": data.get("is_admin", False)})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: str = Depends(security)): # 修正
    """
    JWTトークンから現在のユーザーを取得
    """
    token = credentials
    
    
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"username": username, "is_admin": payload.get("is_admin", False)}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_admin_user(current_user: dict = Depends(get_current_user)):
    """
    管理者権限を確認
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


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
    cache: Annotated[CacheManager, Depends(get_cache_manager)]
) -> DataService:
    """
    Provides a DataService instance for each request.
    
    Note: The 'db' dependency has been removed as DataService no longer uses it directly.
    
    Args:
        cache: Shared cache manager instance.
    
    Returns:
        DataService: A new DataService instance.
    """
    return DataService(cache_manager=cache)


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
# current_userの型ヒント
CurrentUser = Annotated[dict, Depends(get_current_user)]
AdminUser = Annotated[dict, Depends(get_admin_user)]