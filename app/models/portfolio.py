import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Constants
from app.constants import TRADING_DAYS_PER_YEAR



class PortfolioCalculator:
    """
    A pure business logic class that performs portfolio calculations.
    
    All methods are static and do not maintain any state. This design allows
    for easy testing and reuse across different contexts.
    
    The calculator assumes:
    - Daily price data
    - 252 trading days per year for annualization
    - Risk-free rates are annualized
    """

    @staticmethod
    def calculate_annual_returns(data: pd.DataFrame) -> pd.Series:
        """
        Calculates annualized average returns from daily price data.

        Args:
            data: DataFrame with daily prices, with tickers as columns.
                  Must contain at least 2 rows of data.

        Returns:
            A Series of annualized average returns for each ticker.
            
        Raises:
            ValueError: If data is empty or has fewer than 2 rows.
            
        Examples:
            >>> data = pd.DataFrame({'AAPL': [100, 101, 102]})
            >>> returns = PortfolioCalculator.calculate_annual_returns(data)
            >>> returns['AAPL'] > 0
            True
        """
        if data.empty or len(data) < 2:
            raise ValueError("Data must contain at least 2 rows for return calculation")
        
        returns = data.pct_change().dropna()
        
        if returns.empty:
            raise ValueError("Unable to calculate returns from provided data")
        
        avg_returns = returns.mean() * TRADING_DAYS_PER_YEAR
        return avg_returns

    @staticmethod
    def calculate_covariance_matrix(data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the annualized covariance matrix of returns.

        Args:
            data: DataFrame with daily prices, with tickers as columns.
                  Must contain at least 2 rows of data.

        Returns:
            The annualized covariance matrix of returns.
            
        Raises:
            ValueError: If data is empty or has fewer than 2 rows.
        """
        if data.empty or len(data) < 2:
            raise ValueError("Data must contain at least 2 rows for covariance calculation")
        
        returns = data.pct_change().dropna()
        
        if returns.empty:
            raise ValueError("Unable to calculate returns from provided data")
        
        cov_matrix = returns.cov() * TRADING_DAYS_PER_YEAR
        return cov_matrix

    @staticmethod
    def calculate_portfolio_volatility(
        weights: np.ndarray, cov_matrix: pd.DataFrame
    ) -> float:
        """
        Calculates the annualized portfolio volatility (risk).

        Args:
            weights: An array of weights for each asset in the portfolio.
                     Must sum to approximately 1.0.
            cov_matrix: The annualized covariance matrix of asset returns.

        Returns:
            The annualized portfolio volatility (always non-negative).
            
        Raises:
            ValueError: If weights shape doesn't match covariance matrix dimensions.
            
        Examples:
            >>> weights = np.array([0.5, 0.5])
            >>> cov = pd.DataFrame([[0.04, 0.01], [0.01, 0.09]])
            >>> vol = PortfolioCalculator.calculate_portfolio_volatility(weights, cov)
            >>> vol >= 0
            True
        """
        if len(weights) != len(cov_matrix):
            raise ValueError(
                f"Weights length ({len(weights)}) must match "
                f"covariance matrix dimension ({len(cov_matrix)})"
            )
        
        # Calculate portfolio variance
        variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        
        # Handle numerical errors that might result in slightly negative variance
        if variance < 0:
            if variance < -1e-10:  # Tolerance for numerical errors
                logger.warning(
                    f"Portfolio variance is significantly negative: {variance}. "
                    "This may indicate a problem with the covariance matrix."
                )
            variance = 0.0
        
        volatility = np.sqrt(variance)
        return float(volatility)

    @staticmethod
    def calculate_portfolio_return(
        weights: np.ndarray, avg_returns: pd.Series
    ) -> float:
        """
        Calculates the annualized portfolio return.

        Args:
            weights: An array of weights for each asset in the portfolio.
            avg_returns: A Series of annualized average returns for each asset.

        Returns:
            The annualized portfolio return.
            
        Raises:
            ValueError: If weights length doesn't match returns length.
        """
        if len(weights) != len(avg_returns):
            raise ValueError(
                f"Weights length ({len(weights)}) must match "
                f"returns length ({len(avg_returns)})"
            )
        
        portfolio_return = np.sum(avg_returns.values * weights)
        return float(portfolio_return)

    @staticmethod
    def calculate_sharpe_ratio(
        portfolio_return: float, 
        portfolio_volatility: float, 
        risk_free_rate: float
    ) -> float:
        """
        Calculates the Sharpe ratio of the portfolio.

        The Sharpe ratio measures risk-adjusted return. Higher values indicate
        better risk-adjusted performance.

        Args:
            portfolio_return: The annualized return of the portfolio.
            portfolio_volatility: The annualized volatility of the portfolio.
            risk_free_rate: The annualized risk-free rate of return.

        Returns:
            The Sharpe ratio. Returns -np.inf if volatility is zero or negative.
            
        Examples:
            >>> PortfolioCalculator.calculate_sharpe_ratio(0.10, 0.15, 0.02)
            0.5333333333333333
            >>> PortfolioCalculator.calculate_sharpe_ratio(0.10, 0.0, 0.02)
            -inf
        """
        if portfolio_volatility <= 0:
            logger.debug("Sharpe ratio undefined for zero or negative volatility")
            return -np.inf
        
        sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility
        return float(sharpe)

    @staticmethod
    def calculate_downside_deviation(
        weights: np.ndarray, 
        daily_returns: pd.DataFrame, 
        risk_free_rate: float
    ) -> float:
        """
        Calculates the annualized portfolio downside deviation.
        
        Downside deviation only considers returns below the risk-free rate,
        making it a more relevant risk measure for investors primarily concerned
        with losses.

        Args:
            weights: An array of weights for each asset in the portfolio.
            daily_returns: DataFrame of daily returns for each asset.
            risk_free_rate: The annualized target return (typically risk-free rate).

        Returns:
            The annualized downside deviation. Returns 0.0 if no downside returns.
            
        Raises:
            ValueError: If weights length doesn't match daily_returns columns.
        """
        if len(weights) != len(daily_returns.columns):
            raise ValueError(
                f"Weights length ({len(weights)}) must match "
                f"number of assets ({len(daily_returns.columns)})"
            )
        
        # Calculate daily portfolio returns
        portfolio_returns = daily_returns.dot(weights)
        
        # Convert annualized risk-free rate to daily rate
        daily_risk_free_rate = (1 + risk_free_rate) ** (1 / TRADING_DAYS_PER_YEAR) - 1
        
        # Filter for returns below the risk-free rate (downside returns)
        downside_returns = portfolio_returns[portfolio_returns < daily_risk_free_rate]
        
        if len(downside_returns) == 0:
            logger.debug("No downside returns found; downside deviation is 0")
            return 0.0
        
        # Calculate squared deviations from the daily risk-free rate
        squared_deviations = (downside_returns - daily_risk_free_rate) ** 2
        
        # Calculate mean and annualize
        mean_squared_deviation = squared_deviations.mean()
        annualized_downside_deviation = np.sqrt(mean_squared_deviation * TRADING_DAYS_PER_YEAR)
        
        return float(annualized_downside_deviation)

    @staticmethod
    def calculate_sortino_ratio(
        portfolio_return: float, 
        downside_deviation: float, 
        risk_free_rate: float
    ) -> float:
        """
        Calculates the Sortino ratio of the portfolio.
        
        The Sortino ratio is similar to the Sharpe ratio but uses downside
        deviation instead of standard deviation, focusing only on downside risk.

        Args:
            portfolio_return: The annualized return of the portfolio.
            downside_deviation: The annualized downside deviation of the portfolio.
            risk_free_rate: The annualized risk-free rate of return.

        Returns:
            The Sortino ratio. Returns np.inf if downside deviation is zero.
            
        Examples:
            >>> PortfolioCalculator.calculate_sortino_ratio(0.10, 0.08, 0.02)
            1.0
            >>> PortfolioCalculator.calculate_sortino_ratio(0.10, 0.0, 0.02)
            inf
        """
        if downside_deviation <= 0:
            logger.debug("Sortino ratio infinite for zero or negative downside deviation")
            return np.inf
        
        sortino = (portfolio_return - risk_free_rate) / downside_deviation
        return float(sortino)

    @staticmethod
    def validate_weights(weights: np.ndarray, tolerance: float = 1e-6) -> bool:
        """
        Validates that portfolio weights sum to approximately 1.0.
        
        Args:
            weights: Array of portfolio weights.
            tolerance: Acceptable deviation from 1.0.
            
        Returns:
            True if weights are valid, False otherwise.
            
        Examples:
            >>> weights = np.array([0.5, 0.5])
            >>> PortfolioCalculator.validate_weights(weights)
            True
            >>> weights = np.array([0.6, 0.6])
            >>> PortfolioCalculator.validate_weights(weights)
            False
        """
        weight_sum = np.sum(weights)
        is_valid = abs(weight_sum - 1.0) <= tolerance
        
        if not is_valid:
            logger.warning(f"Weights sum to {weight_sum}, expected 1.0 ± {tolerance}")
        
        return is_valid