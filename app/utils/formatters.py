from typing import Dict, Any

def format_market_cap(cap: int | float | None) -> str:
    """
    Formats a large number representing market capitalization into a human-readable
    string with a suffix (T, B, M, K).

    Args:
        cap: The market capitalization value.

    Returns:
        A formatted string (e.g., "1.23T", "45.6B") or "N/A" if input is invalid.
    """
    if cap is None or not isinstance(cap, (int, float)) or cap == 0:
        return "N/A"
    if cap >= 1_000_000_000_000:
        return f"{cap / 1_000_000_000_000:.2f}T"
    if cap >= 1_000_000_000:
        return f"{cap / 1_000_000_000:.2f}B"
    if cap >= 1_000_000:
        return f"{cap / 1_000_000:.2f}M"
    if cap >= 1_000:
        return f"{cap / 1_000:.2f}K"
    return str(int(cap))

def generate_etf_summary(
    info: Dict[str, Any], etf_static_data: Dict[str, Any], basic_info: Dict[str, Any]
) -> str:
    """
    Generates a descriptive summary string for an ETF based on its available data.
    This function was originally in Japanese and has been translated and adapted.

    Args:
        info: Dynamic data from yfinance `etf.info`.
        etf_static_data: Static data from the project's CSV file.
        basic_info: A dictionary containing basic info like fund family.

    Returns:
        A formatted summary string.
    """
    summary_parts = []
    fund_family = basic_info.get("fundFamily")
    if fund_family and fund_family != "N/A":
        summary_parts.append(f"Provided by '{fund_family}',")

    category = info.get("category")
    asset_class = etf_static_data.get("asset_class")
    region = etf_static_data.get("region")

    description_parts = []
    if region and region.strip():
        description_parts.append(f"investing in the [{region.strip()}] region")
    if asset_class and asset_class.strip():
        description_parts.append(f"within the [{asset_class.strip()}] asset class.")

    if description_parts:
        summary_parts.append(" ".join(description_parts))

    if category and category != "N/A":
        summary_parts.append(f"It is classified under the '{category}' category.")

    style = etf_static_data.get("style")
    if style and style.strip():
        summary_parts.append(f"Its investment style is '{style.strip()}'.")

    theme = etf_static_data.get("theme")
    if theme and theme.strip():
        summary_parts.append(f"It focuses on the '{theme.strip()}' theme.")

    if not summary_parts:
        return "No detailed summary is available."
    
    # Join all parts into a single coherent sentence.
    full_summary = " ".join(summary_parts)
    # Capitalize the first letter and ensure it ends with a period.
    return full_summary[0].upper() + full_summary[1:]
