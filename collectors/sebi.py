"""SEBI enforcement orders / press releases.

SEBI doesn't publish a clean RSS for orders, but its press release listing
page is parseable. For an MVP we fetch the press release feed page and
return items whose text matches any of our portfolio company names.

A more robust pipeline would scrape:
  https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=6&smid=0
but for the free MVP we stick with the press release RSS feed.
"""

from __future__ import annotations

import logging
from typing import Any

import feedparser
import httpx

log = logging.getLogger(__name__)

SEBI_PRESS_RSS = "https://www.sebi.gov.in/sebirss.xml"


async def fetch_sebi_mentions(
    client: httpx.AsyncClient,
    company_names: list[str],
) -> dict[str, list[dict[str, Any]]]:
    """Return a dict of company_name -> list of matching SEBI press items."""
    out: dict[str, list[dict[str, Any]]] = {n: [] for n in company_names}
    try:
        r = await client.get(SEBI_PRESS_RSS, timeout=15.0)
        r.raise_for_status()
        feed = feedparser.parse(r.text)
    except Exception as e:  # noqa: BLE001
        log.warning("SEBI RSS fetch failed: %s", e)
        return out

    for entry in feed.entries:
        title = (entry.get("title") or "").lower()
        summary = (entry.get("summary") or "").lower()
        haystack = f"{title} {summary}"
        for name in company_names:
            # Match on first significant token of the name to keep recall up
            tokens = [t for t in name.lower().split() if len(t) > 3]
            if any(tok in haystack for tok in tokens[:2]):
                out[name].append(
                    {
                        "title": entry.get("title"),
                        "url": entry.get("link"),
                        "published_at": entry.get("published"),
                        "summary": entry.get("summary", "")[:500],
                    }
                )
    return out
