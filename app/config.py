import logging
import os
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from pydantic import model_validator
from pydantic_settings import BaseSettings
from google.cloud import secretmanager

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Secret Manager Helper ---
def _get_secret(project_id: str, secret_id: str, version_id: str = "latest") -> Optional[str]:
    """Retrieves a secret from Google Cloud Secret Manager."""
    if not project_id:
        return None
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.warning(f"Could not access secret {secret_id} in project {project_id}: {e}")
        return None


# --- Path Constants ---
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
ETF_LIST_PATH = BASE_DIR / "etf_list.csv"


# --- Pydantic Settings ---
class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and Secret Manager.
    """
    # .env file fields
    database_url: str
    secret_key: Optional[str] = None
    algorithm: str
    access_token_expire_minutes: int
    ga_measurement_id: str = ""
    affiliate_ibkr_url: str = ""
    affiliate_schwab_url: str = ""
    affiliate_fidelity_url: str = ""
    affiliate_rakuten_url: str = ""
    affiliate_sbi_url: str = ""
    affiliate_monex_url: str = ""

    # Existing fields with default values
    app_name: str = "ETF Portfolio Analysis API"
    app_version: str = "0.1.0"
    risk_free_rate: float = 0.02
    cache_ttl_seconds: int = 3600
    project_id: str = os.getenv("GCLOUD_PROJECT", "") # GAE provides GCLOUD_PROJECT
    cors_origins: List[str] = [
        "https://etf-risk-return-map-project.an.r.appspot.com",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    rate_limit_per_minute: str = "60/minute"

    @model_validator(mode='after')
    def set_secret_key(self) -> 'Settings':
        """Load secret_key from Secret Manager if in production, else from .env."""
        if self.project_id:
            logger.info(f"GCP environment detected (Project ID: {self.project_id}). Attempting to load secret from Secret Manager.")
            secret_value = _get_secret(self.project_id, "SECRET_KEY")
            if secret_value:
                self.secret_key = secret_value
                logger.info("Successfully loaded SECRET_KEY from Secret Manager.")

        if not self.secret_key:
            logger.warning("Could not load SECRET_KEY from Secret Manager or it was not available. Falling back to .env file.")
            # If secret_key is still not set, pydantic-settings would have loaded it from .env
            # If it's still None after that, it means it was not in .env either.
            if not self.secret_key:
                 raise ValueError("SECRET_KEY not found in Secret Manager or .env file.")
        return self

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
    ... (rest of the function is unchanged)
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