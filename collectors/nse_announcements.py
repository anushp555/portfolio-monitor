"""Fetch NSE corporate announcements (equity segment).

NSE blocks unauth'd direct API calls. Workflow:
  1. GET https://www.nseindia.com/  -> stash cookies in the client jar
  2. GET https://www.nseindia.com/get-quotes/equity?symbol=XYZ -> warm symbol
  3. GET the announcements API with same cookies + browser headers

Endpoint:
  https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=XYZ
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

NSE_HOME = "https://www.nseindia.com/"
NSE_QUOTE = "https://www.nseindia.com/get-quotes/equity"
NSE_ANN = "https://www.nseindia.com/api/corporate-announcements"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
}


async def _warm_cookies(client: httpx.AsyncClient, symbol: str) -> bool:
    try:
        await client.get(NSE_HOME, headers=HEADERS, timeout=15.0)
        await client.get(
            NSE_QUOTE, params={"symbol": symbol}, headers=HEADERS, timeout=15.0
        )
        return True
    except Exception as e:  # noqa: BLE001
        log.warning("NSE cookie warm-up failed for %s: %s", symbol, e)
        return False


async def fetch_nse_announcements(
    client: httpx.AsyncClient,
    symbol: str,
    from_date: dt.date,
    to_date: dt.date,
) -> list[dict[str, Any]]:
    """Return announcements for a symbol between two dates (inclusive)."""
    if not await _warm_cookies(client, symbol):
        return []

    params = {
        "index": "equities",
        "symbol": symbol,
        "from_date": from_date.strftime("%d-%m-%Y"),
        "to_date": to_date.strftime("%d-%m-%Y"),
    }

    try:
        r = await client.get(NSE_ANN, params=params, headers=HEADERS, timeout=20.0)
        r.raise_for_status()
        items = r.json()
    except Exception as e:  # noqa: BLE001
        log.warning("NSE announcements fetch failed for %s: %s", symbol, e)
        return []

    if not isinstance(items, list):
        items = items.get("data", []) if isinstance(items, dict) else []

    out: list[dict[str, Any]] = []
    for it in items:
        out.append(
            {
                "headline": (it.get("desc") or it.get("subject") or "").strip(),
                "category": it.get("smIndustry") or it.get("subject"),
                "more_info": (it.get("attchmntText") or "").strip(),
                "pdf_url": it.get("attchmntFile"),
                "attached_at": it.get("an_dt") or it.get("sort_date"),
                "source": "NSE",
            }
        )
    return out
