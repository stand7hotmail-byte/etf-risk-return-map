from typing import List, Dict, Any

import numpy as np
import pandas as pd

from app.services.data_service import DataService


class SimulationService:
    """
    Performs financial simulations like Monte Carlo and Dollar-Cost Averaging (DCA).
    """

    def __init__(self, data_service: DataService):
        """
        Initializes the SimulationService.

        Args:
            data_service: An instance of DataService to fetch price data.
        """
        self.data_service = data_service

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
        """
        price_data = self.data_service.fetch_historical_data(tickers, period)
        daily_returns = price_data.pct_change().dropna()

        portfolio_returns = daily_returns.dot(weights)
        mean_return = portfolio_returns.mean()
        std_dev = portfolio_returns.std()

        simulation_results = np.zeros((num_simulations, simulation_days))
        for i in range(num_simulations):
            random_returns = np.random.normal(mean_return, std_dev, simulation_days)
            simulation_results[i, :] = random_returns

        # Calculate cumulative returns for each simulation
        final_returns = np.prod(1 + simulation_results, axis=1) - 1

        var_95 = np.percentile(final_returns, 5)
        cvar_95 = final_returns[final_returns <= var_95].mean()

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
        """
        price_data = self.data_service.fetch_historical_data(tickers, period)
        
        # Ensure weights match the order of columns in the data
        w_array = np.array([weights.get(ticker, 0.0) for ticker in price_data.columns])
        w_array /= np.sum(w_array)

        if frequency == "monthly":
            resample_freq = "MS"  # Month Start
        elif frequency == "quarterly":
            resample_freq = "QS-JAN"  # Quarter Start
        else:
            raise ValueError("Invalid frequency specified")

        investment_dates = price_data.resample(resample_freq).first().index
        
        total_shares = np.zeros(len(price_data.columns))
        total_invested = 0.0
        portfolio_value_ts = pd.Series(index=price_data.index, dtype=float)
        
        inv_date_idx = 0
        for date, prices in price_data.iterrows():
            if inv_date_idx < len(investment_dates) and date >= investment_dates[inv_date_idx]:
                total_invested += investment_amount
                additional_shares = (investment_amount * w_array) / prices.values
                total_shares += additional_shares
                inv_date_idx += 1
            
            portfolio_value_ts[date] = np.dot(total_shares, prices.values)

        final_value = portfolio_value_ts.iloc[-1]
        return {
            "dates": portfolio_value_ts.index.strftime("%Y-%m-%d").tolist(),
            "portfolio_values": portfolio_value_ts.fillna(0).tolist(),
            "total_invested": total_invested,
            "final_value": final_value,
            "profit_loss": final_value - total_invested,
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
        """
        freq_num = 12 if frequency == "monthly" else 4
        num_steps = years * freq_num

        periodic_return = (1 + portfolio_return) ** (1 / freq_num) - 1
        periodic_risk = portfolio_risk / np.sqrt(freq_num)

        all_scenarios = np.zeros((num_simulations, num_steps + 1))
        total_invested_steps = np.zeros(num_steps + 1)

        for i in range(num_simulations):
            portfolio_value = 0
            total_invested = 0
            
            for t in range(1, num_steps + 1):
                portfolio_value += investment_amount
                total_invested += investment_amount
                
                market_return = np.random.normal(periodic_return, periodic_risk)
                portfolio_value *= 1 + market_return
                
                all_scenarios[i, t] = portfolio_value
                if i == 0: # Only need to calculate this once
                    total_invested_steps[t] = total_invested

        mean_scenario = np.mean(all_scenarios, axis=0)
        upper_scenario = np.percentile(all_scenarios, 95, axis=0)
        lower_scenario = np.percentile(all_scenarios, 5, axis=0)

        time_labels = [f"{(t / freq_num):.2f}" for t in range(num_steps + 1)]

        return {
            "time_labels": time_labels,
            "mean_scenario": mean_scenario.tolist(),
            "upper_scenario": upper_scenario.tolist(),
            "lower_scenario": lower_scenario.tolist(),
            "total_invested": total_invested_steps.tolist(),
        }
