"""
WARP Formatters (utils/formatters.py)

Display formatting helpers for currency, dates, scores, etc.
"""

from datetime import date


def format_currency(amount: float, currency: str = "EUR") -> str:
    """Format a number as currency."""
    if currency == "EUR":
        return f"€{amount:,.2f}"
    return f"${amount:,.2f}"


def format_date(d: date) -> str:
    """Format a date as YYYY-MM-DD."""
    if d is None:
        return "N/A"
    return d.strftime("%Y-%m-%d")


def format_score(score: float) -> str:
    """Format a WARP score with color coding hint."""
    if score is None or str(score) == "nan":
        return "N/A"
    
    if score < 3.0:
        return f"🔴 {score:.1f}/10 (Critical)"
    elif score < 5.0:
        return f"🟠 {score:.1f}/10 (High Risk)"
    elif score < 7.0:
        return f"🟡 {score:.1f}/10 (Medium Risk)"
    else:
        return f"🟢 {score:.1f}/10 (Low Risk)"


def format_alert_level(level: str) -> str:
    """Format an alert level with icon."""
    icon_map = {
        "red": "🔴 RED (Overdue)",
        "amber": "🟡 AMBER (Imminent)",
        "proactive": "🟠 PROACTIVE (High Risk)",
        "ok": "🟢 OK (On Track)"
    }
    return icon_map.get(level, "⚪ UNKNOWN")


def format_percentage(value: float) -> str:
    """Format a percentage."""
    return f"{value:.1f}%"


def format_days(days: int) -> str:
    """Format days with context."""
    if days < 0:
        return f"🔴 {abs(days)} days overdue"
    elif days == 0:
        return "🟡 Due today"
    elif days <= 3:
        return f"🟡 {days} days"
    elif days <= 10:
        return f"🟠 {days} days"
    else:
        return f"🟢 {days} days"