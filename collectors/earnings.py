"""Earnings / event calendar via NSE.

NSE exposes an event calendar at:
  https://www.nseindia.com/api/event-calendar

Returns Board Meetings (results, dividends, fund-raising, etc.). We filter for
upcoming or recent results events.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

NSE_EVENT_URL = "https://www.nseindia.com/api/event-calendar"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar",
}


async def fetch_events(
    client: httpx.AsyncClient,
    symbol: str,
    window_days: int = 7,
) -> list[dict[str, Any]]:
    """Return events for a symbol within +/- window_days of today.

    Requires the same cookie warm-up the announcements module does. We expect
    callers to share an httpx.AsyncClient that's already warm.
    """
    today = dt.date.today()
    params = {
        "index": "equities",
        "from_date": (today - dt.timedelta(days=window_days)).strftime("%d-%m-%Y"),
        "to_date": (today + dt.timedelta(days=window_days)).strftime("%d-%m-%Y"),
    }
    try:
        r = await client.get(NSE_EVENT_URL, params=params, headers=HEADERS, timeout=15.0)
        r.raise_for_status()
        data = r.json()
    except Exception as e:  # noqa: BLE001
        log.warning("NSE event calendar fetch failed: %s", e)
        return []

    if not isinstance(data, list):
        return []

    matches = [
        {
            "subject": ev.get("subject"),
            "purpose": ev.get("purpose"),
            "date": ev.get("date"),
            "details": ev.get("bm_desc"),
        }
        for ev in data
        if (ev.get("symbol") or "").upper() == symbol.upper()
    ]
    return matches
