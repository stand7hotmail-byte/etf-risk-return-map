
# Mock google.cloud.secretmanager before app is imported
from unittest import mock

import numpy as np
import pandas as pd
import pytest

from app.config import RISK_FREE_RATE
from app.models.portfolio import PortfolioCalculator

with mock.patch("google.cloud.secretmanager.SecretManagerServiceClient"):
    pass # This block is now empty or can be removed if not needed for other mocks
@pytest.fixture
def mock_data() -> dict:
    """Provide mock data for testing calculation functions."""
    # Using a small, predictable dataset
    avg_returns = pd.Series([0.1, 0.2, 0.15], index=["ETF1", "ETF2", "ETF3"])

    # Simple covariance matrix
    cov_matrix = pd.DataFrame([
        [0.10, 0.02, 0.01],
        [0.02, 0.15, 0.03],
        [0.01, 0.03, 0.12]
    ], index=["ETF1", "ETF2", "ETF3"], columns=["ETF1", "ETF2", "ETF3"])

    # Equal weights
    weights = np.array([1/3, 1/3, 1/3])

    return {
        "avg_returns": avg_returns,
        "cov_matrix": cov_matrix,
        "weights": weights
    }

def test_portfolio_return(mock_data: dict) -> None:
    """Tests the PortfolioCalculator.calculate_portfolio_return method."""
    p_return = PortfolioCalculator.calculate_portfolio_return(mock_data["weights"], mock_data["avg_returns"])
    # Expected: (0.1 + 0.2 + 0.15) / 3 = 0.45 / 3 = 0.15
    assert np.isclose(p_return, 0.15)

def test_portfolio_volatility(mock_data: dict) -> None:
    """Tests the PortfolioCalculator.calculate_portfolio_volatility method."""
    p_volatility = PortfolioCalculator.calculate_portfolio_volatility(mock_data["weights"], mock_data["cov_matrix"])
    # Expected calculation:
    # w.T * C * w =
    # [1/3, 1/3, 1/3] * [[0.10, 0.02, 0.01], [0.02, 0.15, 0.03],
    #                    [0.01, 0.03, 0.12]] * [1/3, 1/3, 1/3]^T
    # = [1/3, 1/3, 1/3] * [0.13/3, 0.20/3, 0.16/3]^T
    # = (0.13 + 0.20 + 0.16) / 9 = 0.49 / 9 = 0.05444...
    # sqrt(0.05444...) = 0.2333...
    expected_volatility = np.sqrt(0.05444444444)
    assert np.isclose(p_volatility, expected_volatility)

def test_portfolio_sharpe_ratio(mock_data: dict) -> None:
    """Tests the PortfolioCalculator.calculate_sharpe_ratio method."""
    p_return = PortfolioCalculator.calculate_portfolio_return(mock_data["weights"], mock_data["avg_returns"])
    p_volatility = PortfolioCalculator.calculate_portfolio_volatility(mock_data["weights"], mock_data["cov_matrix"])
    sharpe_ratio = PortfolioCalculator.calculate_sharpe_ratio(
        p_return, p_volatility, RISK_FREE_RATE
    )
    expected_sharpe = (p_return - RISK_FREE_RATE) / p_volatility
    assert np.isclose(sharpe_ratio, expected_sharpe)

def test_portfolio_sharpe_ratio_zero_volatility(mock_data: dict) -> None:
    """Tests that sharpe ratio handles zero volatility."""
    zero_cov_matrix = pd.DataFrame(np.zeros((3,3)), columns=["ETF1", "ETF2", "ETF3"])
    p_return = PortfolioCalculator.calculate_portfolio_return(mock_data["weights"], mock_data["avg_returns"])
    p_volatility = PortfolioCalculator.calculate_portfolio_volatility(mock_data["weights"], zero_cov_matrix)
    sharpe_ratio = PortfolioCalculator.calculate_sharpe_ratio(
        p_return, p_volatility, RISK_FREE_RATE
    )

    # Should return -inf as per the function's logic to avoid division by zero
    assert sharpe_ratio == -np.inf
