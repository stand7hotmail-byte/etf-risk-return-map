from typing import List, Dict, Any, Tuple, Callable

import numpy as np
import pandas as pd
from scipy.optimize import minimize, OptimizeResult

from app.models.portfolio import PortfolioCalculator
from app.services.data_service import DataService
from app.utils.calculations import filter_efficient_frontier


class OptimizationService:
    """
    Performs portfolio optimization calculations like finding the efficient frontier.
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

    def calculate_efficient_frontier(
        self, tickers: List[str], period: str
    ) -> Dict[str, Any]:
        """
        Calculates the efficient frontier and the tangency portfolio (max Sharpe ratio).

        Args:
            tickers: A list of ETF tickers.
            period: The historical data period (e.g., "5y").

        Returns:
            A dictionary containing individual ETF data, frontier points,
            and the tangency portfolio details.
        """
        if not tickers:
            return {
                "etf_data": [],
                "frontier_points": [],
                "tangency_portfolio": None,
                "tangency_portfolio_weights": {},
            }

        # 1. Fetch data and calculate basic metrics
        price_data = self.data_service.fetch_historical_data(tickers, period)
        final_tickers = price_data.columns.tolist()
        avg_returns = self.calculator.calculate_annual_returns(price_data)
        cov_matrix = self.calculator.calculate_covariance_matrix(price_data)
        daily_returns = price_data.pct_change().dropna()

        num_assets = len(final_tickers)
        bounds = tuple([(0.0, 1.0)] * num_assets)
        initial_weights = np.array([1.0 / num_assets] * num_assets)

        # 2. Find the tangency portfolio (maximize Sharpe ratio)
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
            p_return = self.calculator.calculate_portfolio_return(tangency_w, avg_returns)
            p_volatility = self.calculator.calculate_portfolio_volatility(tangency_w, cov_matrix)
            sharpe = self.calculator.calculate_sharpe_ratio(p_return, p_volatility, self.risk_free_rate)
            
            tangency_portfolio = {"Return": p_return, "Risk": p_volatility, "SharpeRatio": sharpe}
            tangency_weights = dict(zip(final_tickers, tangency_w))

        # 3. Generate points for the efficient frontier curve
        frontier_points = []
        target_returns = np.linspace(avg_returns.min(), avg_returns.max(), 20)

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
            if min_vol_result.success:
                p_return = self.calculator.calculate_portfolio_return(min_vol_result.x, avg_returns)
                p_volatility = self.calculator.calculate_portfolio_volatility(min_vol_result.x, cov_matrix)
                frontier_points.append({"Return": p_return, "Risk": p_volatility})

        # 4. Calculate individual ETF risk/return
        etf_data = []
        for ticker in final_tickers:
            etf_return = avg_returns[ticker]
            etf_risk = np.sqrt(cov_matrix.loc[ticker, ticker])
            etf_data.append({"Ticker": ticker, "Return": etf_return, "Risk": etf_risk})

        return {
            "etf_data": etf_data,
            "frontier_points": filter_efficient_frontier(frontier_points),
            "tangency_portfolio": tangency_portfolio,
            "tangency_portfolio_weights": tangency_weights,
        }

    def _run_optimization(
        self,
        objective_func: Callable,
        initial_weights: np.ndarray,
        bounds: Tuple,
        constraints: Tuple,
    ) -> OptimizeResult:
        """A wrapper for the scipy.optimize.minimize function."""
        return minimize(
            objective_func,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

    def _minimize_negative_sharpe(self, avg_returns: pd.Series, cov_matrix: pd.DataFrame) -> Callable:
        """Returns a function that calculates the negative Sharpe ratio for the optimizer."""
        def objective(weights: np.ndarray) -> float:
            p_return = self.calculator.calculate_portfolio_return(weights, avg_returns)
            p_volatility = self.calculator.calculate_portfolio_volatility(weights, cov_matrix)
            sharpe = self.calculator.calculate_sharpe_ratio(p_return, p_volatility, self.risk_free_rate)
            return -sharpe
        return objective

    def _minimize_volatility(self, cov_matrix: pd.DataFrame) -> Callable:
        """Returns a function that calculates portfolio volatility for the optimizer."""
        def objective(weights: np.ndarray) -> float:
            return self.calculator.calculate_portfolio_volatility(weights, cov_matrix)
        return objective

    def optimize_by_target_return(
        self, tickers: List[str], target_return: float, period: str
    ) -> Dict[str, Any]:
        """
        Optimizes a portfolio to achieve a target return while minimizing risk.

        Args:
            tickers: A list of ETF tickers.
            target_return: The desired annual return for the portfolio.
            period: The historical data period.

        Returns:
            A dictionary with the optimized portfolio's metrics or an error.
        """
        price_data = self.data_service.fetch_historical_data(tickers, period)
        final_tickers = price_data.columns.tolist()
        avg_returns = self.calculator.calculate_annual_returns(price_data)
        cov_matrix = self.calculator.calculate_covariance_matrix(price_data)
        daily_returns = price_data.pct_change().dropna()[final_tickers]

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

        if result.success:
            weights = result.x
            p_return = self.calculator.calculate_portfolio_return(weights, avg_returns)
            p_volatility = self.calculator.calculate_portfolio_volatility(weights, cov_matrix)
            downside_dev = self.calculator.calculate_downside_deviation(weights, daily_returns, self.risk_free_rate)
            sortino = self.calculator.calculate_sortino_ratio(p_return, downside_dev, self.risk_free_rate)
            
            return {
                "Risk": p_volatility,
                "Return": p_return,
                "SortinoRatio": sortino,
                "weights": dict(zip(final_tickers, weights)),
            }
        else:
            return {
                "error": "Could not find an optimal portfolio for the given target return.",
                "details": result.message,
            }

    def optimize_by_target_risk(
        self, tickers: List[str], target_risk: float, period: str
    ) -> Dict[str, Any]:
        """
        Optimizes a portfolio to match a target risk level while maximizing return.

        Args:
            tickers: A list of ETF tickers.
            target_risk: The desired annual volatility for the portfolio.
            period: The historical data period.

        Returns:
            A dictionary with the optimized portfolio's metrics or an error.
        """
        price_data = self.data_service.fetch_historical_data(tickers, period)
        final_tickers = price_data.columns.tolist()
        avg_returns = self.calculator.calculate_annual_returns(price_data)
        cov_matrix = self.calculator.calculate_covariance_matrix(price_data)
        daily_returns = price_data.pct_change().dropna()[final_tickers]

        num_assets = len(final_tickers)
        bounds = tuple([(0.0, 1.0)] * num_assets)
        initial_weights = np.array([1.0 / num_assets] * num_assets)

        constraints = (
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w: self.calculator.calculate_portfolio_volatility(w, cov_matrix) - target_risk},
        )

        def maximize_return(weights: np.ndarray) -> float:
            return -self.calculator.calculate_portfolio_return(weights, avg_returns)

        result = self._run_optimization(
            objective_func=maximize_return,
            initial_weights=initial_weights,
            bounds=bounds,
            constraints=constraints,
        )

        if result.success:
            weights = result.x
            p_return = self.calculator.calculate_portfolio_return(weights, avg_returns)
            p_volatility = self.calculator.calculate_portfolio_volatility(weights, cov_matrix)
            downside_dev = self.calculator.calculate_downside_deviation(weights, daily_returns, self.risk_free_rate)
            sortino = self.calculator.calculate_sortino_ratio(p_return, downside_dev, self.risk_free_rate)

            return {
                "Risk": p_volatility,
                "Return": p_return,
                "SortinoRatio": sortino,
                "weights": dict(zip(final_tickers, weights)),
            }
        else:
            return {
                "error": "Could not find an optimal portfolio for the given target risk.",
                "details": result.message,
            }

    def calculate_custom_portfolio_metrics(
        self, tickers: List[str], weights_dict: Dict[str, float], period: str
    ) -> Dict[str, Any]:
        """
        Calculates the risk and return for a portfolio with custom weights.

        Args:
            tickers: A list of ETF tickers.
            weights_dict: A dictionary mapping tickers to their weights.
            period: The historical data period.

        Returns:
            A dictionary containing the portfolio's risk and return, or an error.
        """
        price_data = self.data_service.fetch_historical_data(tickers, period)
        final_tickers = price_data.columns.tolist()
        
        if not final_tickers:
            return {"error": "Could not fetch data for any of the provided tickers."}

        avg_returns = self.calculator.calculate_annual_returns(price_data)
        cov_matrix = self.calculator.calculate_covariance_matrix(price_data)

        # Align weights to the order of tickers in the processed data
        weights_array = np.array([weights_dict.get(ticker, 0.0) for ticker in final_tickers])
        
        # Normalize weights to ensure they sum to 1
        if np.sum(weights_array) > 0:
            weights_array = weights_array / np.sum(weights_array)
        else:
            return {"error": "Sum of weights cannot be zero."}

        p_return = self.calculator.calculate_portfolio_return(weights_array, avg_returns)
        p_volatility = self.calculator.calculate_portfolio_volatility(weights_array, cov_matrix)

        return {"Risk": p_volatility, "Return": p_return}
