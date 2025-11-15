import io
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.utils.cache import CacheManager


class DataService:
    """
    Manages data fetching and preparation from various sources like yfinance and CSV.
    """

    def __init__(self, db: Session, cache_manager: CacheManager):
        """
        Initializes the DataService.

        Args:
            db: The SQLAlchemy database session.
            cache_manager: The cache manager instance for caching yfinance data.
        """
        self.db = db
        self.cache = cache_manager

    def fetch_historical_data(
        self, tickers: List[str], period: str, interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetches and prepares historical stock data from yfinance.

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
            return pd.DataFrame()

        data = yf.download(tickers, period=period, interval=interval, group_by="ticker")

        if data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Could not download data for tickers: {tickers} and period: {period}.",
            )

        # Extract 'Close' prices, handling single vs. multi-ticker downloads
        if len(tickers) > 1:
            if "Close" in data.columns.levels[1]:
                data = data.xs("Close", level="Price", axis=1)
            else: # Sometimes yfinance returns a flat structure even for multiple tickers
                data = data[[col for col in data.columns if col in tickers]]
        else:
            data = data[["Close"]]
            data.columns = tickers

        # Clean data
        data = data.dropna(axis=1, how="all")  # Drop tickers with no data
        data = data.ffill().bfill()  # Fill missing values

        if data.empty:
            raise HTTPException(
                status_code=404, detail="No valid data remained after cleaning."
            )

        return data

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
            return cached_info

        try:
            etf = yf.Ticker(ticker)
            info = etf.info
            if not info or info.get("quoteType") == "NONE":
                raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}.")
            
            self.cache.set(cache_key, info)
            return info
        except Exception as e:
            # This can catch various yfinance/network errors
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch details for {ticker} from yfinance: {e}",
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
                raise ValueError("Not enough data to calculate returns.")

            annual_returns = returns.mean() * 252
            annual_volatility = returns.std() * np.sqrt(252)

            result_df = pd.DataFrame({
                "Return": annual_returns,
                "Risk": annual_volatility,
                "Ticker": annual_returns.index,
            })

            return result_df.to_dict(orient="records")

        except (ValueError, KeyError) as e:
            raise HTTPException(status_code=400, detail=f"Error processing CSV: {e}")
        except Exception as e:
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
        price_data = self.fetch_historical_data(tickers, period)
        daily_returns = price_data.pct_change().dropna()
        cumulative_returns = (1 + daily_returns).cumprod() - 1

        return {
            "dates": cumulative_returns.index.strftime("%Y-%m-%d").tolist(),
            "cumulative_returns": {
                col: cumulative_returns[col].tolist() for col in cumulative_returns.columns
            },
        }

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
        price_data = self.fetch_historical_data(tickers, period)
        daily_returns = price_data.pct_change().dropna()
        correlation_matrix = daily_returns.corr()

        return {
            "x": correlation_matrix.columns.tolist(),
            "y": correlation_matrix.index.tolist(),
            "z": correlation_matrix.values.tolist(),
        }
