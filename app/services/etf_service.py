from typing import Dict, Any

from app.services.data_service import DataService
from app.utils.formatters import format_market_cap, generate_etf_summary


class ETFService:
    """
    Manages ETF information, combining static definitions with live data.
    """

    def __init__(self, etf_definitions: Dict[str, Any], data_service: DataService):
        """
        Initializes the ETFService.

        Args:
            etf_definitions: A dictionary of static ETF data, keyed by ticker.
            data_service: An instance of DataService to fetch live data.
        """
        self.data_service = data_service
        self.etf_definitions = etf_definitions


    def get_all_etfs(self) -> Dict[str, Any]:
        """
        Returns the complete list of static ETF definitions.

        Returns:
            A dictionary of all ETF definitions, keyed by ticker.
        """
        return self.etf_definitions

    def get_etf_details(self, ticker: str) -> Dict[str, Any]:
        """
        Retrieves and combines static and dynamic details for a given ETF.

        Args:
            ticker: The ETF ticker symbol.

        Returns:
            A dictionary containing formatted details for the ETF.
        """
        # 1. Get static data from our definitions
        etf_static_data = self.etf_definitions.get(ticker, {})
        if not etf_static_data:
            # Optionally, you could still proceed and only show dynamic data
            # For now, we assume an ETF must be in our list to get details
            # This can be changed based on product requirements.
            pass # Allow fetching details even if not in our static list

        # 2. Get live data from the data service (which handles caching)
        info = self.data_service.get_etf_info(ticker)

        # 3. Combine and format the data
        basic_info = {
            "longName": info.get("longName", "N/A"),
            "fundFamily": info.get("fundFamily", "N/A"),
        }

        key_metrics = {
            "AUM": format_market_cap(info.get("totalAssets")),
            "Yield": (
                f'{info.get("trailingAnnualDividendYield", 0) * 100:.2f}%'
                if info.get("trailingAnnualDividendYield")
                else "N/A"
            ),
            "Expense Ratio": (
                f'{info.get("annualReportExpenseRatio", 0) * 100:.2f}%'
                if info.get("annualReportExpenseRatio")
                else "N/A"
            ),
            "YTD Return": (
                f'{info.get("ytdReturn", 0) * 100:.2f}%'
                if info.get("ytdReturn")
                else "N/A"
            ),
            "Beta": f'{info.get("beta", "N/A")}',
            "52wk High": info.get("fiftyTwoWeekHigh", "N/A"),
            "52wk Low": info.get("fiftyTwoWeekLow", "N/A"),
        }

        # 4. Generate the summary
        basic_info["generatedSummary"] = generate_etf_summary(
            info, etf_static_data, basic_info
        )

        return {
            "basicInfo": basic_info,
            "keyMetrics": key_metrics,
        }
