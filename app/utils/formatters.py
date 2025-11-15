from typing import Dict, Any, Optional


def format_market_cap(cap: int | float | None) -> str:
    """
    Formats market capitalization into human-readable string with suffix.

    Args:
        cap: The market capitalization value.

    Returns:
        Formatted string (e.g., "1.23T", "45.6B") or "N/A" if invalid.
        
    Examples:
        >>> format_market_cap(1_500_000_000_000)
        '1.50T'
        >>> format_market_cap(2_300_000_000)
        '2.30B'
        >>> format_market_cap(None)
        'N/A'
    """
    if cap is None or not isinstance(cap, (int, float)) or cap <= 0:
        return "N/A"
    
    thresholds = [
        (1_000_000_000_000, "T"),
        (1_000_000_000, "B"),
        (1_000_000, "M"),
        (1_000, "K"),
    ]
    
    for threshold, suffix in thresholds:
        if cap >= threshold:
            return f"{cap / threshold:.2f}{suffix}"
    
    return str(int(cap))


def format_percentage(value: float | None, decimals: int = 2) -> str:
    """
    Formats a decimal value as a percentage string.
    
    Args:
        value: Decimal value (e.g., 0.0523 for 5.23%).
        decimals: Number of decimal places.
        
    Returns:
        Formatted percentage string or "N/A" if invalid.
        
    Examples:
        >>> format_percentage(0.0523)
        '5.23%'
        >>> format_percentage(None)
        'N/A'
    """
    if value is None or not isinstance(value, (int, float)):
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def generate_etf_summary(
    info: Dict[str, Any],
    etf_static_data: Dict[str, Any],
    basic_info: Dict[str, Any]
) -> str:
    """
    Generates a descriptive summary for an ETF based on available data.

    Args:
        info: Dynamic data from yfinance `etf.info`.
        etf_static_data: Static data from the project's CSV file.
        basic_info: Dictionary containing basic info like fund family.

    Returns:
        Formatted summary string.
        
    Examples:
        >>> info = {"category": "Large Blend"}
        >>> static = {"asset_class": "Equity", "region": "US"}
        >>> basic = {"fundFamily": "Vanguard"}
        >>> summary = generate_etf_summary(info, static, basic)
        >>> "Vanguard" in summary
        True
    """
    parts = []
    
    # Fund family
    fund_family = basic_info.get("fundFamily")
    if fund_family and fund_family != "N/A":
        parts.append(f"Provided by '{fund_family}'")
    
    # Region and asset class
    region = etf_static_data.get("region", "").strip()
    asset_class = etf_static_data.get("asset_class", "").strip()
    
    if region or asset_class:
        desc = []
        if region:
            desc.append(f"the {region} region")
        if asset_class:
            desc.append(f"the {asset_class} asset class")
        
        if desc:
            parts.append(f"investing in {' within '.join(desc)}")
    
    # Category
    category = info.get("category")
    if category and category != "N/A":
        parts.append(f"classified under '{category}'")
    
    # Style
    style = etf_static_data.get("style", "").strip()
    if style:
        parts.append(f"with a '{style}' investment style")
    
    # Theme
    theme = etf_static_data.get("theme", "").strip()
    if theme:
        parts.append(f"focusing on '{theme}'")
    
    if not parts:
        return "No detailed summary is available."
    
    # Join parts with proper punctuation
    summary = ", ".join(parts) + "."
    return summary.capitalize()