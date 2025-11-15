import numpy as np
import pandas as pd

class PortfolioCalculator:
    """
    A pure business logic class that performs portfolio calculations.
    All methods are static and do not maintain any state.
    """

    @staticmethod
    def calculate_annual_returns(data: pd.DataFrame) -> pd.Series:
        """
        Calculates annualized average returns from daily price data.

        Args:
            data: DataFrame with daily prices, with tickers as columns.

        Returns:
            A Series of annualized average returns for each ticker.
        """
        returns = data.pct_change().dropna()
        avg_returns = returns.mean() * 252
        return avg_returns

    @staticmethod
    def calculate_covariance_matrix(data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the annualized covariance matrix of returns.

        Args:
            data: DataFrame with daily prices, with tickers as columns.

        Returns:
            The annualized covariance matrix of returns.
        """
        returns = data.pct_change().dropna()
        cov_matrix = returns.cov() * 252
        return cov_matrix

    @staticmethod
    def calculate_portfolio_volatility(
        weights: np.ndarray, cov_matrix: pd.DataFrame
    ) -> float:
        """
        Calculates the annualized portfolio volatility (risk).

        Args:
            weights: An array of weights for each asset in the portfolio.
            cov_matrix: The annualized covariance matrix of asset returns.

        Returns:
            The annualized portfolio volatility.
        """
        return float(np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))))

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
        """
        return float(np.sum(avg_returns * weights))

    @staticmethod
    def calculate_sharpe_ratio(
        portfolio_return: float, portfolio_volatility: float, risk_free_rate: float
    ) -> float:
        """
        Calculates the Sharpe ratio of the portfolio.

        Args:
            portfolio_return: The annualized return of the portfolio.
            portfolio_volatility: The annualized volatility of the portfolio.
            risk_free_rate: The risk-free rate of return.

        Returns:
            The Sharpe ratio. Returns -np.inf if volatility is zero.
        """
        if portfolio_volatility == 0:
            return -np.inf
        return (portfolio_return - risk_free_rate) / portfolio_volatility

    @staticmethod
    def calculate_downside_deviation(
        weights: np.ndarray, daily_returns: pd.DataFrame, risk_free_rate: float
    ) -> float:
        """
        Calculates the annualized portfolio downside deviation.

        Args:
            weights: An array of weights for each asset in the portfolio.
            daily_returns: DataFrame of daily returns for each asset.
            risk_free_rate: The target return, typically the risk-free rate.

        Returns:
            The annualized downside deviation.
        """
        # Calculate daily portfolio returns
        portfolio_returns = daily_returns.dot(weights)
        
        # Calculate periodic risk-free rate
        periodic_risk_free_rate = (1 + risk_free_rate)**(1/252) - 1
        
        # Filter for returns below the target
        downside_returns = portfolio_returns[portfolio_returns < periodic_risk_free_rate]
        
        if len(downside_returns) == 0:
            return 0.0
            
        # Calculate the squared differences from the target
        squared_diffs = (downside_returns - periodic_risk_free_rate) ** 2
        
        # Calculate the mean of the squared differences and annualize it
        annualized_downside_deviation = np.sqrt(np.mean(squared_diffs)) * np.sqrt(252)
        
        return float(annualized_downside_deviation)

    @staticmethod
    def calculate_sortino_ratio(
        portfolio_return: float, downside_deviation: float, risk_free_rate: float
    ) -> float:
        """
        Calculates the Sortino ratio of the portfolio.

        Args:
            portfolio_return: The annualized return of the portfolio.
            downside_deviation: The annualized downside deviation of the portfolio.
            risk_free_rate: The risk-free rate of return.

        Returns:
            The Sortino ratio. Returns np.inf if downside deviation is zero.
        """
        if downside_deviation == 0:
            return np.inf
        return (portfolio_return - risk_free_rate) / downside_deviation
