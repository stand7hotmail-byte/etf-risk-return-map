import logging
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize, OptimizeResult

from app.models.portfolio import PortfolioCalculator
from app.services.data_service import DataService
from fastapi import HTTPException
from app.utils.calculations import filter_efficient_frontier
from app.schemas import OptimizationResult, PortfolioMetrics, ETFData, EfficientFrontierPoint, TangencyPortfolio
from app.constants import TRADING_DAYS_PER_YEAR

logger = logging.getLogger(__name__)


class OptimizationService:
    """
    Performs portfolio optimization calculations like finding the efficient frontier.
    
    Features:
    - Calculates efficient frontier and tangency portfolio
    - Optimizes portfolio for target return or risk
    - Calculates custom portfolio metrics
    - Integrates with DataService for data fetching and PortfolioCalculator for math
    """

    def __init__(
        self, calculator: PortfolioCalculator, data_service: DataService, risk_free_rate: float
    ):
        """
        Initializes the OptimizationService.

        Args:
            calculator: An instance of PortfolioCalculator for math functions.
            data_service: An instance of DataService to fetch price data.
            risk_free_rate: The risk-free rate for Sharpe ratio calculations.
        """
        self.calculator = calculator
        self.data_service = data_service
        self.risk_free_rate = risk_free_rate
        logger.info("OptimizationService initialized.")

    def _prepare_portfolio_data(
        self, tickers: List[str], period: str
    ) -> Tuple[pd.DataFrame, List[str], pd.Series, pd.DataFrame, pd.DataFrame]:
        """
        Prepares common portfolio data (price data, returns, covariance) for optimization.
        
        Args:
            tickers: List of ETF tickers.
            period: Historical data period.
            
        Returns:
            Tuple containing:
            - price_data: DataFrame of historical close prices.
            - final_tickers: List of tickers after data cleaning.
            - avg_returns: Annualized average returns.
            - cov_matrix: Annualized covariance matrix.
            - daily_returns: DataFrame of daily returns.
            
        Raises:
            HTTPException: If data fetching or calculation fails.
        """
        logger.debug(f"Preparing portfolio data for {len(tickers)} tickers: {tickers}, period: {period}")
        price_data = self.data_service.fetch_historical_data(tickers, period)
        final_tickers = price_data.columns.tolist()

        if not final_tickers:
            raise HTTPException(
                status_code=404, detail="No valid tickers with data found after fetching."
            )

        try:
            avg_returns = self.calculator.calculate_annual_returns(price_data)
            cov_matrix = self.calculator.calculate_covariance_matrix(price_data)
            daily_returns = price_data.pct_change().dropna()[final_tickers]
        except ValueError as e:
            logger.error(f"Error calculating portfolio metrics: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Error calculating portfolio metrics: {e}")
        
        logger.debug(f"Data prepared for {len(final_tickers)} tickers.")
        return price_data, final_tickers, avg_returns, cov_matrix, daily_returns

    def calculate_efficient_frontier(
        self, tickers: List[str], period: str
    ) -> OptimizationResult:
        """
        Calculates the efficient frontier and the tangency portfolio (max Sharpe ratio).

        Args:
            tickers: A list of ETF tickers.
            period: The historical data period (e.g., "5y").

        Returns:
            A dictionary containing individual ETF data, frontier points,
            and the tangency portfolio details.
        """
        logger.info(f"Calculating efficient frontier for {len(tickers)} tickers: {tickers}, period: {period}")
        if not tickers:
            logger.warning("No tickers provided for efficient frontier calculation.")
            return OptimizationResult(
                etf_data=[],
                frontier_points=[],
                tangency_portfolio=None,
                tangency_portfolio_weights={},
            )

        _, final_tickers, avg_returns, cov_matrix, _ = self._prepare_portfolio_data(tickers, period)

        num_assets = len(final_tickers)
        bounds = tuple([(0.0, 1.0)] * num_assets)
        initial_weights = np.array([1.0 / num_assets] * num_assets)

        # 2. Find the tangency portfolio (maximize Sharpe ratio)
        logger.debug("Finding tangency portfolio...")
        max_sharpe_result = self._run_optimization(
            objective_func=self._minimize_negative_sharpe(avg_returns, cov_matrix),
            initial_weights=initial_weights,
            bounds=bounds,
            constraints=({"type": "eq", "fun": lambda w: np.sum(w) - 1},),
        )

        tangency_weights = {}
        tangency_portfolio = None
        if max_sharpe_result.success:
            tangency_w = max_sharpe_result.x
            if self.calculator.validate_weights(tangency_w):
                p_return = self.calculator.calculate_portfolio_return(tangency_w, avg_returns)
                p_volatility = self.calculator.calculate_portfolio_volatility(tangency_w, cov_matrix)
                sharpe = self.calculator.calculate_sharpe_ratio(p_return, p_volatility, self.risk_free_rate)
                
                tangency_portfolio = TangencyPortfolio(Return=float(p_return), Risk=float(p_volatility), SharpeRatio=float(sharpe))
                tangency_weights = {t: float(w) for t, w in zip(final_tickers, tangency_w)}
                logger.info(f"Tangency portfolio found: Sharpe={sharpe:.4f}")
            else:
                logger.warning("Tangency portfolio weights did not sum to 1.0, skipping.")
        else:
            logger.warning(f"Failed to find tangency portfolio: {max_sharpe_result.message}")

        # 3. Generate points for the efficient frontier curve
        logger.debug("Generating efficient frontier points...")
        frontier_points = []
        # Use a wider range for target returns to ensure frontier is well-covered
        min_return = avg_returns.min() * 0.8 if avg_returns.min() < 0 else avg_returns.min() * 0.5
        max_return = avg_returns.max() * 1.2 if avg_returns.max() > 0 else avg_returns.max() * 1.5
        target_returns = np.linspace(min_return, max_return, 30) # Increased points for smoother curve

        for target in target_returns:
            min_vol_result = self._run_optimization(
                objective_func=self._minimize_volatility(cov_matrix),
                initial_weights=initial_weights,
                bounds=bounds,
                constraints=(
                    {"type": "eq", "fun": lambda w: np.sum(w) - 1},
                    {"type": "eq", "fun": lambda w, r=avg_returns, t=target: self.calculator.calculate_portfolio_return(w, r) - t},
                ),
            )
            if min_vol_result.success and self.calculator.validate_weights(min_vol_result.x):
                p_return = self.calculator.calculate_portfolio_return(min_vol_result.x, avg_returns)
                p_volatility = self.calculator.calculate_portfolio_volatility(min_vol_result.x, cov_matrix)
                frontier_points.append(EfficientFrontierPoint(Return=float(p_return), Risk=float(p_volatility)))
        
        filtered_frontier = filter_efficient_frontier(frontier_points)
        logger.info(f"Generated {len(filtered_frontier)} filtered frontier points.")

        # 4. Calculate individual ETF risk/return
        etf_data = []
        for ticker in final_tickers:
            etf_return = avg_returns[ticker]
            etf_risk = np.sqrt(cov_matrix.loc[ticker, ticker]) # Individual volatility is sqrt of variance
            etf_data.append(ETFData(Ticker=ticker, Return=float(etf_return), Risk=float(etf_risk)))
        
        logger.info("Efficient frontier calculation complete.")
        return OptimizationResult(
            etf_data=etf_data,
            frontier_points=filtered_frontier,
            tangency_portfolio=tangency_portfolio,
            tangency_portfolio_weights=tangency_weights,
        )

    def _run_optimization(
        self,
        objective_func: Callable,
        initial_weights: np.ndarray,
        bounds: Tuple,
        constraints: Tuple,
    ) -> OptimizeResult:
        """
        A wrapper for the scipy.optimize.minimize function with error handling.
        """
        try:
            result = minimize(
                objective_func,
                initial_weights,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
            )
            if not result.success:
                logger.warning(f"Optimization failed: {result.message}")
            return result
        except Exception as e:
            logger.error(f"Optimization encountered an unexpected error: {e}", exc_info=True)
            # Return a failed result object
            class FailedResult:
                success = False
                message = str(e)
                x = np.array([]) # Ensure x is an array even on failure
            return FailedResult()

    def _minimize_negative_sharpe(self, avg_returns: pd.Series, cov_matrix: pd.DataFrame) -> Callable:
        """Returns a function that calculates the negative Sharpe ratio for the optimizer."""
        def objective(weights: np.ndarray) -> float:
            if not self.calculator.validate_weights(weights): # Basic check before heavy calculation
                return np.inf # Penalize invalid weights
            p_return = self.calculator.calculate_portfolio_return(weights, avg_returns)
            p_volatility = self.calculator.calculate_portfolio_volatility(weights, cov_matrix)
            sharpe = self.calculator.calculate_sharpe_ratio(p_return, p_volatility, self.risk_free_rate)
            return -sharpe
        return objective

    def _minimize_volatility(self, cov_matrix: pd.DataFrame) -> Callable:
        """Returns a function that calculates portfolio volatility for the optimizer."""
        def objective(weights: np.ndarray) -> float:
            if not self.calculator.validate_weights(weights): # Basic check before heavy calculation
                return np.inf # Penalize invalid weights
            return self.calculator.calculate_portfolio_volatility(weights, cov_matrix)
        return objective

    def optimize_by_target_return(
        self, tickers: List[str], target_return: float, period: str
    ) -> PortfolioMetrics:
        """
        Optimizes a portfolio to achieve a target return while minimizing risk.

        Args:
            tickers: A list of ETF tickers.
            target_return: The desired annual return for the portfolio.
            period: The historical data period.

        Returns:
            A dictionary with the optimized portfolio's metrics or an error.
        """
        logger.info(f"Optimizing by target return ({target_return:.2%}) for {len(tickers)} tickers: {tickers}, period: {period}")
        _, final_tickers, avg_returns, cov_matrix, daily_returns = self._prepare_portfolio_data(tickers, period)

        num_assets = len(final_tickers)
        bounds = tuple([(0.0, 1.0)] * num_assets)
        initial_weights = np.array([1.0 / num_assets] * num_assets)

        constraints = (
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w: self.calculator.calculate_portfolio_return(w, avg_returns) - target_return},
        )

        result = self._run_optimization(
            objective_func=self._minimize_volatility(cov_matrix),
            initial_weights=initial_weights,
            bounds=bounds,
            constraints=constraints,
        )

        if result.success and self.calculator.validate_weights(result.x):
            weights = result.x
            p_return = self.calculator.calculate_portfolio_return(weights, avg_returns)
            p_volatility = self.calculator.calculate_portfolio_volatility(weights, cov_matrix)
            downside_dev = self.calculator.calculate_downside_deviation(weights, daily_returns, self.risk_free_rate)
            sortino = self.calculator.calculate_sortino_ratio(p_return, downside_dev, self.risk_free_rate)
            
            logger.info(f"Optimization by target return successful. Risk: {p_volatility:.4f}, Return: {p_return:.4f}")
            return PortfolioMetrics(
                Risk=float(p_volatility),
                Return=float(p_return),
                SortinoRatio=float(sortino),
                weights={t: float(w) for t, w in zip(final_tickers, weights)},
            )
        else:
            error_msg = f"Could not find an optimal portfolio for the given target return ({target_return:.2%})."
            logger.warning(f"{error_msg} Details: {result.message}")
            return PortfolioMetrics(
                Risk=0.0,
                Return=0.0,
                error=error_msg,
                details=str(result.message),
            )

    def optimize_by_target_risk(
        self, tickers: List[str], target_risk: float, period: str
    ) -> PortfolioMetrics:
        """
        Optimizes a portfolio to match a target risk level while maximizing return.

        Args:
            tickers: A list of ETF tickers.
            target_risk: The desired annual volatility for the portfolio.
            period: The historical data period.

        Returns:
            A dictionary with the optimized portfolio's metrics or an error.
        """
        logger.info(f"Optimizing by target risk ({target_risk:.2%}) for {len(tickers)} tickers: {tickers}, period: {period}")
        _, final_tickers, avg_returns, cov_matrix, daily_returns = self._prepare_portfolio_data(tickers, period)

        num_assets = len(final_tickers)
        bounds = tuple([(0.0, 1.0)] * num_assets)
        initial_weights = np.array([1.0 / num_assets] * num_assets)

        constraints = (
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w: self.calculator.calculate_portfolio_volatility(w, cov_matrix) - target_risk},
        )

        def maximize_return(weights: np.ndarray) -> float:
            if not self.calculator.validate_weights(weights): # Basic check
                return np.inf # Penalize invalid weights
            return -self.calculator.calculate_portfolio_return(weights, avg_returns)

        result = self._run_optimization(
            objective_func=maximize_return,
            initial_weights=initial_weights,
            bounds=bounds,
            constraints=constraints,
        )

        if result.success and self.calculator.validate_weights(result.x):
            weights = result.x
            p_return = self.calculator.calculate_portfolio_return(weights, avg_returns)
            p_volatility = self.calculator.calculate_portfolio_volatility(weights, cov_matrix)
            downside_dev = self.calculator.calculate_downside_deviation(weights, daily_returns, self.risk_free_rate)
            sortino = self.calculator.calculate_sortino_ratio(p_return, downside_dev, self.risk_free_rate)

            logger.info(f"Optimization by target risk successful. Risk: {p_volatility:.4f}, Return: {p_return:.4f}")
            return PortfolioMetrics(
                Risk=float(p_volatility),
                Return=float(p_return),
                SortinoRatio=float(sortino),
                weights={t: float(w) for t, w in zip(final_tickers, weights)},
            )
        else:
            error_msg = f"Could not find an optimal portfolio for the given target risk ({target_risk:.2%})."
            logger.warning(f"{error_msg} Details: {result.message}")
            return PortfolioMetrics(
                Risk=0.0,
                Return=0.0,
                error=error_msg,
                details=str(result.message),
            )

    def calculate_custom_portfolio_metrics(
        self, tickers: List[str], weights_dict: Dict[str, float], period: str
    ) -> PortfolioMetrics:
        """
        Calculates the risk and return for a portfolio with custom weights.

        Args:
            tickers: A list of ETF tickers.
            weights_dict: A dictionary mapping tickers to their weights.
            period: The historical data period.

        Returns:
            A dictionary containing the portfolio's risk and return, or an error.
        """
        logger.info(f"Calculating custom portfolio metrics for {len(tickers)} tickers: {tickers}, period: {period}")
        _, final_tickers, avg_returns, cov_matrix, _ = self._prepare_portfolio_data(tickers, period)
        
        # Align weights to the order of tickers in the processed data
        weights_array = np.array([weights_dict.get(ticker, 0.0) for ticker in final_tickers])
        
        # Normalize weights to ensure they sum to 1
        if np.sum(weights_array) > 0:
            weights_array = weights_array / np.sum(weights_array)
        else:
            logger.error("Sum of custom portfolio weights is zero or negative.")
            return PortfolioMetrics(Risk=0.0, Return=0.0, error="Sum of weights cannot be zero or negative.")

        if not self.calculator.validate_weights(weights_array):
            logger.warning("Custom portfolio weights did not sum to 1.0 after normalization.")
            # Proceed anyway, but log the warning. Or raise an error if strict validation is needed.

        p_return = self.calculator.calculate_portfolio_return(weights_array, avg_returns)
        p_volatility = self.calculator.calculate_portfolio_volatility(weights_array, cov_matrix)

        logger.info(f"Custom portfolio metrics calculated. Risk: {p_volatility:.4f}, Return: {p_return:.4f}")
        return PortfolioMetrics(Risk=float(p_volatility), Return=float(p_return))