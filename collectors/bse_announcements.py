"""Fetch BSE corporate announcements for a given scrip code.

The BSE exposes a public JSON API at:
  https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w

Returns a list of announcements with: headline, category, pdf_link, attached_at.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

BSE_URL = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Referer": "https://www.bseindia.com/",
    "Accept": "application/json, text/plain, */*",
}


def _fmt(d: dt.date) -> str:
    return d.strftime("%Y%m%d")


async def fetch_bse_announcements(
    client: httpx.AsyncClient,
    scrip_code: str,
    from_date: dt.date,
    to_date: dt.date,
) -> list[dict[str, Any]]:
    """Fetch announcements between two dates (inclusive). Dates in IST."""
    params = {
        "strCat": "-1",
        "strPrevDate": _fmt(from_date),
        "strToDate": _fmt(to_date),
        "strScrip": scrip_code,
        "strSearch": "P",
        "strType": "C",
    }
    try:
        r = await client.get(BSE_URL, params=params, headers=HEADERS, timeout=20.0)
        r.raise_for_status()
        data = r.json()
    except Exception as e:  # noqa: BLE001
        log.warning("BSE fetch failed for %s: %s", scrip_code, e)
        return []

    # BSE sometimes returns a string (error page / rate-limit message) instead
    # of the expected JSON object. Guard against that so one bad response
    # doesn't crash the whole pipeline.
    if not isinstance(data, dict):
        log.warning(
            "BSE returned non-dict for %s (got %s); skipping",
            scrip_code, type(data).__name__,
        )
        return []

    items = data.get("Table", []) or []
    if not isinstance(items, list):
        log.warning("BSE 'Table' not a list for %s; skipping", scrip_code)
        return []

    out: list[dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        pdf_name = it.get("ATTACHMENTNAME") or ""
        pdf_url = (
            f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{pdf_name}"
            if pdf_name
            else None
        )
        out.append(
            {
                "headline": (it.get("HEADLINE") or "").strip(),
                "category": it.get("CATEGORYNAME") or it.get("CATEGORY"),
                "subcategory": it.get("SUBCATNAME"),
                "more_info": (it.get("MORE") or "").strip(),
                "pdf_url": pdf_url,
                "attached_at": it.get("News_submission_dt") or it.get("DT_TM"),
                "source": "BSE",
            }
        )
    return out
