"""Shared helpers used by all collectors."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import yaml
from dateutil import tz

IST = tz.gettz("Asia/Kolkata")
ROOT = Path(__file__).resolve().parent.parent


def load_portfolio() -> list[dict[str, Any]]:
    """Read portfolio.yaml from project root."""
    with open(ROOT / "portfolio.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("stocks", [])


def now_ist() -> dt.datetime:
    return dt.datetime.now(tz=IST)


def previous_trading_day(today: dt.date | None = None) -> dt.date:
    """Approximate previous trading day. Skips weekends only.

    NSE holidays are skipped naively here; for production parity, fetch from
    nseindia.com/api/holiday-master and cache. For an MVP this is fine because
    on a holiday the script will simply find no price data and the LLM will
    flag the stock as 'no movement reported'.
    """
    today = today or now_ist().date()
    d = today - dt.timedelta(days=1)
    while d.weekday() >= 5:  # Sat=5, Sun=6
        d -= dt.timedelta(days=1)
    return d


def iso(d: dt.date | dt.datetime) -> str:
    if isinstance(d, dt.datetime):
        return d.isoformat()
    return d.isoformat()
