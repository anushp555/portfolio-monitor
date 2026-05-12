"""Shared helpers used by all collectors."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import yaml
from dateutil import tz

IST = tz.gettz("Asia/Kolkata")
ROOT = Path(__file__).resolve().parent.parent

# NSE holiday calendar for 2026 (trading holidays only).
# Source: NSE circulars. Update annually.
NSE_HOLIDAYS_2026 = {
    dt.date(2026, 1, 26),   # Republic Day
    dt.date(2026, 2, 19),   # Mahashivratri
    dt.date(2026, 3, 6),    # Holi
    dt.date(2026, 3, 31),   # Eid-Ul-Fitr
    dt.date(2026, 4, 3),    # Good Friday
    dt.date(2026, 4, 14),   # Ambedkar Jayanti
    dt.date(2026, 5, 1),    # Maharashtra Day
    dt.date(2026, 5, 11),   # Buddha Purnima
    dt.date(2026, 8, 15),   # Independence Day
    dt.date(2026, 8, 27),   # Ganesh Chaturthi
    dt.date(2026, 10, 2),   # Gandhi Jayanti
    dt.date(2026, 10, 21),  # Diwali (tentative)
    dt.date(2026, 11, 4),   # Guru Nanak Jayanti
    dt.date(2026, 12, 25),  # Christmas
}


def load_portfolio() -> list[dict[str, Any]]:
    """Read portfolio.yaml from project root."""
    with open(ROOT / "portfolio.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("stocks", [])


def now_ist() -> dt.datetime:
    return dt.datetime.now(tz=IST)


def is_trading_day(d: dt.date) -> bool:
    """True if d is a Mon-Fri and not an NSE holiday."""
    if d.weekday() >= 5:
        return False
    if d in NSE_HOLIDAYS_2026:
        return False
    return True


def previous_trading_day(today: dt.date | None = None) -> dt.date:
    """Calendar-based estimate of previous trading day.

    Skips weekends AND NSE 2026 holidays. The actual trading day used by the
    pipeline is derived from yfinance price data (see derive_trading_day);
    this function is just a starting hint.
    """
    today = today or now_ist().date()
    d = today - dt.timedelta(days=1)
    while not is_trading_day(d):
        d -= dt.timedelta(days=1)
    return d


def derive_trading_day(prices: dict[str, Any]) -> dt.date | None:
    """Pick the most common 'date' across all price_action entries.

    yfinance returns the actual last available trading bar for each symbol.
    Taking the mode handles edge cases where some symbols haven't traded
    in days (suspended, delisted) while others have fresh data.
    """
    from collections import Counter

    dates: list[str] = []
    for entry in prices.values():
        d = entry.get("date") if isinstance(entry, dict) else None
        if d:
            dates.append(d)
    if not dates:
        return None
    most_common, _ = Counter(dates).most_common(1)[0]
    try:
        return dt.date.fromisoformat(most_common)
    except ValueError:
        return None


def iso(d: dt.date | dt.datetime) -> str:
    if isinstance(d, dt.datetime):
        return d.isoformat()
    return d.isoformat()
