import logging
import os
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import pandas as pd
from pydantic_settings import BaseSettings

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Path Constants ---
# Assuming structure: project/app/config.py
BASE_DIR = Path(__file__).resolve().parent.parent  # Goes up to project root
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
ETF_LIST_PATH = BASE_DIR / "etf_list.csv"


# --- Pydantic Settings ---
class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    app_name: str = "ETF Portfolio Analysis API"
    risk_free_rate: float = 0.02
    cache_ttl_seconds: int = 3600
    project_id: str = ""
    cors_origins: List[str] = [
        "https://etf-risk-return-map-project.an.r.appspot.com",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    rate_limit_per_minute: str = "60/minute"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


@lru_cache()
def get_settings() -> Settings:
    """
    Returns the application settings as a dependency.
    The result is cached to avoid re-reading environment variables on every call.
    """
    return Settings()


# --- Derived Constants ---
settings = get_settings()
RISK_FREE_RATE: float = settings.risk_free_rate
CACHE_TTL_SECONDS: int = settings.cache_ttl_seconds
CACHE_TTL: timedelta = timedelta(seconds=CACHE_TTL_SECONDS)


# --- ETF Definitions Loading ---
def load_etf_definitions(file_path: Path) -> Dict[str, Dict[str, str]]:
    """
    Loads ETF definitions from the specified CSV file into a dictionary.

    Args:
        file_path: The path to the CSV file.

    Returns:
        A dictionary mapping ETF tickers to their details.

    Raises:
        ValueError: If the required 'ticker' column is missing.
    """
    if not file_path.exists():
        logger.warning(f"ETF definitions file not found at: {file_path}")
        return {}

    try:
        df = pd.read_csv(file_path, encoding='utf-8')

        if "ticker" not in df.columns:
            raise ValueError("Required column 'ticker' not found in ETF list CSV.")

        # Ensure all optional columns exist, filling missing ones with empty strings
        optional_cols = ['asset_class', 'region', 'name', 'style', 'size', 'sector', 'theme']
        for col in optional_cols:
            if col not in df.columns:
                df[col] = ''
        
        # Fill NaN values with empty strings
        df.fillna('', inplace=True)

        # Set ticker as index and convert to dictionary
        df.set_index('ticker', inplace=True)
        definitions = df.to_dict(orient='index')
        
        logger.info(f"Successfully loaded {len(definitions)} ETF definitions.")
        return definitions

    except (ValueError, Exception) as e:
        logger.error(f"Error loading ETF definitions: {e}")
        return {}

# --- Global ETF Definitions ---
ETF_DEFINITIONS: Dict[str, Dict[str, str]] = load_etf_definitions(ETF_LIST_PATH)


def get_all_etf_tickers() -> List[str]:
    """
    Returns a list of all available ETF tickers.
    
    Returns:
        List[str]: A list of ETF ticker symbols.
    """
    return list(ETF_DEFINITIONS.keys())