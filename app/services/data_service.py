import io
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from fastapi import HTTPException
from sqlalchemy.orm import Session  # Keep for now, might be used later

from app.utils.cache import CacheManager

logger = logging.getLogger(__name__)


class DataService:
    """
    Manages data fetching and preparation from various sources like yfinance and CSV.
    
    Features:
    - Fetches historical data with caching
    - Retrieves ETF details with caching
    - Loads and analyzes CSV data
    - Calculates historical performance and correlation matrices
    """

    def __init__(self, cache_manager: CacheManager):
        """
        Initializes the DataService.

        Args:
            cache_manager: The cache manager instance for caching yfinance data.
        """
        # self.db = db  # Removed as per instructions, not currently used
        self.cache = cache_manager
        logger.info("DataService initialized with cache manager.")

    def fetch_historical_data(
        self, tickers: List[str], period: str, interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetches and prepares historical stock data from yfinance with caching.

        Args:
            tickers: A list of stock tickers.
            period: The time period for the data (e.g., "5y", "1mo").
            interval: The data interval (e.g., "1d", "1wk").

        Returns:
            A DataFrame containing the 'Close' prices for the given tickers.

        Raises:
            HTTPException: If data cannot be downloaded or is empty after cleaning.
        """
        if not tickers:
            logger.warning("No tickers provided for historical data fetch.")
            return pd.DataFrame()

        cache_key = f"hist_data_{'_'.join(sorted(tickers))}_{period}_{interval}"
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for historical data: {cache_key}")
            return cached_data

        logger.info(f"Fetching historical data for {len(tickers)} tickers: {tickers} for period {period}.")
        try:
            data = yf.download(
                tickers, period=period, interval=interval, group_by="ticker", progress=False
            )

            if data.empty:
                raise ValueError(
                    f"yfinance returned empty data for tickers: {tickers}, period: {period}."
                )

            # Extract 'Close' prices, handling single vs. multi-ticker downloads
            # Use .xs to safely extract 'Close' prices from MultiIndex columns
            # This works for both single and multiple tickers when group_by="ticker"
            data = data.xs("Close", level="Price", axis=1)

            # Ensure column names are just the tickers
            if len(tickers) == 1:
                data.columns = tickers

            

            # Clean data
            initial_cols = data.columns.tolist()
            data = data.dropna(axis=1, how="all")  # Drop tickers with all NaN values
            dropped_cols = set(initial_cols) - set(data.columns.tolist())
            if dropped_cols:
                logger.warning(f"Dropped {len(dropped_cols)} ticker(s) with no data: {dropped_cols}")

            data = data.ffill().bfill()  # Forward-fill and back-fill any remaining NaNs

            if data.empty:
                raise ValueError("No valid data remained after cleaning.")

            self.cache.set(cache_key, data)
            logger.info(f"Successfully fetched and cached historical data for {len(data.columns)} tickers.")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching historical data for {tickers}: {e}", exc_info=True)
            raise HTTPException(
                status_code=503, detail=f"Network error fetching data from yfinance: {e}"
            )
        except ValueError as e:
            logger.warning(f"Data processing error for {tickers}: {e}")
            raise HTTPException(
                status_code=404, detail=f"Could not process data for the given tickers: {e}"
            )
        except HTTPException:
            raise # Re-raise existing HTTPExceptions
        except Exception as e:
            logger.error(f"Unexpected error fetching historical data for {tickers}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"An unexpected error occurred while fetching data: {e}"
            )

    def get_etf_info(self, ticker: str) -> Dict[str, Any]:
        """
        Fetches detailed information for a single ETF, using a cache.

        Args:
            ticker: The ETF ticker symbol.

        Returns:
            A dictionary containing the ETF's information from yfinance.

        Raises:
            HTTPException: If the ticker is invalid or data cannot be fetched.
        """
        cache_key = f"etf_info_{ticker}"
        cached_info = self.cache.get(cache_key)
        if cached_info:
            logger.info(f"Cache hit for ETF info: {ticker}")
            return cached_info

        logger.info(f"Fetching ETF info for {ticker}.")
        try:
            etf = yf.Ticker(ticker)
            info = etf.info
            if not info or info.get("quoteType") == "NONE":
                raise ValueError(f"No data found for ticker {ticker} from yfinance.")

            self.cache.set(cache_key, info)
            logger.info(f"Successfully fetched and cached ETF info for {ticker}.")
            return info
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching ETF info for {ticker}: {e}", exc_info=True)
            raise HTTPException(
                status_code=503, detail=f"Network error fetching ETF details for {ticker}: {e}"
            )
        except ValueError as e:
            logger.warning(f"ETF info not found or invalid for {ticker}: {e}")
            raise HTTPException(status_code=404, detail=f"No details found for ticker {ticker}.")
        except HTTPException:
            raise # Re-raise existing HTTPExceptions
        except Exception as e:
            logger.error(f"Unexpected error fetching ETF info for {ticker}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"An unexpected error occurred while fetching ETF details: {e}"
            )

    def load_and_analyze_csv(self, csv_data: str) -> List[Dict[str, Any]]:
        """
        Loads ETF price data from a CSV string, analyzes it, and calculates
        annualized risk and return for each ticker.

        Args:
            csv_data: A string containing the CSV data.

        Returns:
            A list of dictionaries, each with 'Ticker', 'Risk', and 'Return'.

        Raises:
            HTTPException: If the CSV is malformed or contains no valid data.
        """
        logger.info("Loading and analyzing CSV data.")
        try:
            data = pd.read_csv(io.StringIO(csv_data))

            if "Date" not in data.columns:
                raise ValueError("CSV must contain a 'Date' column.")
            
            data["Date"] = pd.to_datetime(data["Date"])
            data = data.set_index("Date")

            numeric_cols = data.select_dtypes(include=np.number).columns
            if numeric_cols.empty:
                raise ValueError("No numeric ticker columns found in CSV.")
            
            data = data[numeric_cols]
            returns = data.pct_change().dropna()

            if returns.empty:
                raise ValueError("Not enough data to calculate returns from CSV.")

            annual_returns = returns.mean() * 252
            annual_volatility = returns.std() * np.sqrt(252)

            result_df = pd.DataFrame({
                "Return": annual_returns,
                "Risk": annual_volatility,
                "Ticker": annual_returns.index,
            })
            logger.info(f"Successfully analyzed CSV data for {len(result_df)} tickers.")
            return result_df.to_dict(orient="records")

        except (ValueError, KeyError) as e:
            logger.warning(f"Error processing CSV data: {e}")
            raise HTTPException(status_code=400, detail=f"Error processing CSV: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during CSV analysis: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    def get_historical_performance(
        self, tickers: List[str], period: str
    ) -> Dict[str, Any]:
        """
        Retrieves historical performance (cumulative returns) for a list of tickers.

        Args:
            tickers: A list of ETF tickers.
            period: The historical data period.

        Returns:
            A dictionary containing dates and cumulative returns for each ticker.
        """
        logger.info(f"Getting historical performance for {tickers} for period {period}.")
        price_data = self.fetch_historical_data(tickers, period)
        daily_returns = price_data.pct_change().dropna()
        cumulative_returns = (1 + daily_returns).cumprod() - 1

        result = {
            "dates": cumulative_returns.index.strftime("%Y-%m-%d").tolist(),
            "cumulative_returns": {
                col: cumulative_returns[col].tolist() for col in cumulative_returns.columns
            },
        }
        logger.info(f"Successfully retrieved historical performance for {len(tickers)} tickers.")
        return result

    def get_correlation_matrix(
        self, tickers: List[str], period: str
    ) -> Dict[str, Any]:
        """
        Calculates the correlation matrix for a list of tickers.

        Args:
            tickers: A list of ETF tickers.
            period: The historical data period.

        Returns:
            A dictionary formatted for a heatmap (x, y, z data).
        """
        logger.info(f"Calculating correlation matrix for {tickers} for period {period}.")
        price_data = self.fetch_historical_data(tickers, period)
        daily_returns = price_data.pct_change().dropna()
        correlation_matrix = daily_returns.corr()

        result = {
            "x": correlation_matrix.columns.tolist(),
            "y": correlation_matrix.index.tolist(),
            "z": correlation_matrix.values.tolist(),
        }
        logger.info(f"Successfully calculated correlation matrix for {len(tickers)} tickers.")
        return result