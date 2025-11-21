import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from app.services.data_service import DataService

logger = logging.getLogger(__name__)


class SimulationService:
    """
    Performs financial simulations like Monte Carlo and Dollar-Cost Averaging (DCA).
    
    Features:
    - Runs Monte Carlo simulations for portfolio returns.
    - Runs historical Dollar-Cost Averaging (DCA) simulations.
    - Runs future probabilistic DCA simulations.
    - Includes input validation, logging, and robust error handling.
    """

    def __init__(self, data_service: DataService, risk_free_rate: float):
        """
        Initializes the SimulationService.

        Args:
            data_service: An instance of DataService to fetch price data.
            risk_free_rate: The risk-free rate for calculations.
        """
        self.data_service = data_service
        self.risk_free_rate = risk_free_rate
        logger.info("SimulationService initialized.")

    def run_monte_carlo(
        self,
        tickers: List[str],
        weights: np.ndarray,
        period: str,
        num_simulations: int,
        simulation_days: int,
    ) -> Dict[str, Any]:
        """
        Runs a Monte Carlo simulation on a portfolio.

        Args:
            tickers: List of tickers in the portfolio.
            weights: Numpy array of weights for the tickers.
            period: Historical period to base the simulation on.
            num_simulations: The number of simulation runs.
            simulation_days: The number of days to simulate into the future.

        Returns:
            A dictionary with simulation results, including final returns, VaR, and CVaR.
            
        Raises:
            ValueError: If input parameters are invalid.
        """
        logger.info(f"Running Monte Carlo: {num_simulations} simulations, {simulation_days} days, {len(tickers)} tickers.")
        
        if not tickers:
            raise ValueError("Tickers list cannot be empty for Monte Carlo simulation.")
        if not isinstance(weights, np.ndarray) or weights.size == 0 or not np.isclose(np.sum(weights), 1.0):
            raise ValueError("Weights must be a numpy array summing to 1.0.")
        if num_simulations <= 0 or simulation_days <= 0:
            raise ValueError("Number of simulations and simulation days must be positive.")

        price_data = self.data_service.fetch_historical_data(tickers, period)
        
        # Ensure weights align with the fetched data columns
        if len(weights) != len(price_data.columns):
            raise ValueError("Number of weights must match the number of tickers with available data.")

        daily_returns = price_data.pct_change().dropna()

        if daily_returns.empty:
            raise ValueError("Not enough historical data to calculate daily returns for Monte Carlo simulation.")

        portfolio_returns = daily_returns.dot(weights)
        mean_return = portfolio_returns.mean()
        std_dev = portfolio_returns.std()
        logger.debug(f"Portfolio stats: mean={mean_return:.6f}, std={std_dev:.6f}")

        simulation_results = np.zeros((num_simulations, simulation_days))
        for i in range(num_simulations):
            random_returns = np.random.normal(mean_return, std_dev, simulation_days)
            simulation_results[i, :] = random_returns

        # Calculate cumulative returns for each simulation
        final_returns = np.prod(1 + simulation_results, axis=1) - 1

        var_95 = float(np.percentile(final_returns, 5))
        
        returns_below_var = final_returns[final_returns <= var_95]
        cvar_95 = float(returns_below_var.mean()) if len(returns_below_var) > 0 else var_95
        
        logger.info(f"Monte Carlo complete: VaR(95%)={var_95:.4f}, CVaR(95%)={cvar_95:.4f}")
        return {
            "final_returns": final_returns.tolist(),
            "var_95": var_95,
            "cvar_95": cvar_95,
        }

    def run_historical_dca(
        self,
        tickers: List[str],
        weights: Dict[str, float],
        investment_amount: float,
        frequency: str,
        period: str,
    ) -> Dict[str, Any]:
        """
        Runs a historical Dollar-Cost Averaging (DCA) simulation.

        Args:
            tickers: List of tickers to invest in.
            weights: Dictionary of weights for each ticker.
            investment_amount: The amount to invest each period.
            frequency: 'monthly' or 'quarterly'.
            period: The historical period to run the simulation over.

        Returns:
            A dictionary containing the simulation results.
            
        Raises:
            ValueError: If input parameters are invalid.
        """
        logger.info(f"Running historical DCA: {len(tickers)} tickers, ${investment_amount} {frequency}, period={period}.")
        
        if not tickers:
            raise ValueError("Tickers list cannot be empty for historical DCA simulation.")
        if investment_amount <= 0:
            raise ValueError("Investment amount must be positive.")
        if frequency not in ["monthly", "quarterly"]:
            raise ValueError(f"Invalid frequency: {frequency}. Must be 'monthly' or 'quarterly'.")

        price_data = self.data_service.fetch_historical_data(tickers, period)
        
        # Ensure weights align with the fetched data columns
        w_array = np.array([weights.get(ticker, 0.0) for ticker in price_data.columns])
        if np.sum(w_array) <= 0:
            raise ValueError("Sum of weights must be positive.")
        w_array /= np.sum(w_array)  # Normalize
        logger.debug(f"Normalized weights sum: {np.sum(w_array):.6f}")

        if frequency == "monthly":
            resample_freq = "MS"  # Month Start
        elif frequency == "quarterly":
            resample_freq = "QS-JAN"  # Quarter Start
        
        investment_dates = price_data.resample(resample_freq).first().index
        logger.debug(f"Investment dates: {len(investment_dates)} periods.")
        
        total_shares = np.zeros(len(price_data.columns))
        total_invested = 0.0
        portfolio_value_ts = pd.Series(index=price_data.index, dtype=float)
        
        inv_date_idx = 0
        for date, prices in price_data.iterrows():
            if inv_date_idx < len(investment_dates) and date >= investment_dates[inv_date_idx]:
                total_invested += investment_amount
                
                # Handle zero prices to avoid division by zero
                prices_safe = np.where(prices.values > 0, prices.values, np.inf)
                additional_shares = (investment_amount * w_array) / prices_safe
                
                # Handle potential inf/nan from division by inf
                additional_shares = np.nan_to_num(additional_shares, nan=0.0, posinf=0.0)
                
                total_shares += additional_shares
                inv_date_idx += 1
            
            portfolio_value_ts[date] = np.dot(total_shares, prices.values)

        final_value = float(portfolio_value_ts.iloc[-1])
        profit_loss = float(final_value - total_invested)
        
        logger.info(f"Historical DCA complete: Invested=${total_invested:.2f}, Final=${final_value:.2f}, P/L=${profit_loss:.2f}")
        return {
            "dates": portfolio_value_ts.index.strftime("%Y-%m-%d").tolist(),
            "portfolio_values": portfolio_value_ts.fillna(0).tolist(),
            "total_invested": float(total_invested),
            "final_value": final_value,
            "profit_loss": profit_loss,
        }

    def run_future_dca(
        self,
        portfolio_return: float,
        portfolio_risk: float,
        investment_amount: float,
        frequency: str,
        years: int,
        num_simulations: int = 500,
    ) -> Dict[str, Any]:
        """
        Runs a forward-looking, probabilistic DCA simulation.

        Args:
            portfolio_return: Expected annual return of the portfolio.
            portfolio_risk: Expected annual risk (volatility) of the portfolio.
            investment_amount: The amount to invest each period.
            frequency: 'monthly' or 'quarterly'.
            years: Number of years to simulate.
            num_simulations: Number of Monte Carlo simulations to run.

        Returns:
            A dictionary with the results, including mean and percentile scenarios.
            
        Raises:
            ValueError: If input parameters are invalid.
        """
        logger.info(f"Running future DCA: {num_simulations} simulations, {years} years, ${investment_amount} {frequency}.")
        
        if portfolio_return is None or portfolio_risk is None:
            raise ValueError("Portfolio return and risk must be provided.")
        if investment_amount <= 0 or years <= 0 or num_simulations <= 0:
            raise ValueError("Investment amount, years, and number of simulations must be positive.")
        if frequency not in ["monthly", "quarterly"]:
            raise ValueError(f"Invalid frequency: {frequency}. Must be 'monthly' or 'quarterly'.")

        freq_num = 12 if frequency == "monthly" else 4
        num_steps = years * freq_num

        periodic_return = (1 + portfolio_return) ** (1 / freq_num) - 1
        periodic_risk = portfolio_risk / np.sqrt(freq_num)
        logger.debug(f"Periodic stats: return={periodic_return:.6f}, risk={periodic_risk:.6f}")

        all_scenarios = np.zeros((num_simulations, num_steps + 1))
        total_invested_steps = np.zeros(num_steps + 1)

        for i in range(num_simulations):
            portfolio_value = 0.0
            total_invested = 0.0
            
            for t in range(1, num_steps + 1):
                portfolio_value += investment_amount
                total_invested += investment_amount
                
                market_return = np.random.normal(periodic_return, periodic_risk)
                portfolio_value *= 1 + market_return
                
                all_scenarios[i, t] = portfolio_value
                if i == 0: # Only calculate total_invested_steps once
                    total_invested_steps[t] = total_invested

        mean_scenario = np.mean(all_scenarios, axis=0)
        upper_scenario = np.percentile(all_scenarios, 95, axis=0)
        lower_scenario = np.percentile(all_scenarios, 5, axis=0)

        time_labels = [f"{(t / freq_num):.2f}" for t in range(num_steps + 1)]
        
        logger.info(f"Future DCA complete: Final mean value=${mean_scenario[-1]:.2f}")
        return {
            "time_labels": time_labels,
            "mean_scenario": mean_scenario.tolist(),
            "upper_scenario": upper_scenario.tolist(),
            "lower_scenario": lower_scenario.tolist(),
            "total_invested": total_invested_steps.tolist(),
            "final_mean_value": float(mean_scenario[-1]),
        }