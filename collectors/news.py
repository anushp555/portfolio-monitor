"""Fetch news for a stock using free RSS feeds.

Sources:
  - Google News RSS (search-based, India edition)
  - Moneycontrol RSS (market news, broad — filtered by company name match)

Google News RSS lets you build a search URL like:
  https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en
"""

from __future__ import annotations

import datetime as dt
import logging
import re
from typing import Any
from urllib.parse import quote_plus

import feedparser
import httpx

log = logging.getLogger(__name__)

GNEWS_URL = "https://news.google.com/rss/search"


def _build_query(name: str, symbol: str) -> str:
    # Quote the company name to match the exact phrase, OR the ticker
    return f'"{name}" OR "{symbol}"'


def _parse_entry_date(entry: Any) -> dt.datetime | None:
    if getattr(entry, "published_parsed", None):
        return dt.datetime(*entry.published_parsed[:6], tzinfo=dt.timezone.utc)
    if getattr(entry, "updated_parsed", None):
        return dt.datetime(*entry.updated_parsed[:6], tzinfo=dt.timezone.utc)
    return None


async def fetch_news(
    client: httpx.AsyncClient,
    name: str,
    symbol: str,
    since: dt.datetime,
    max_items: int = 8,
) -> list[dict[str, Any]]:
    """Return news items published at or after `since` (UTC)."""
    query = _build_query(name, symbol)
    params = {
        "q": query,
        "hl": "en-IN",
        "gl": "IN",
        "ceid": "IN:en",
    }
    url = f"{GNEWS_URL}?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"

    try:
        r = await client.get(url, timeout=20.0)
        r.raise_for_status()
        feed = feedparser.parse(r.text)
    except Exception as e:  # noqa: BLE001
        log.warning("Google News RSS failed for %s: %s", symbol, e)
        return []

    items: list[dict[str, Any]] = []
    for entry in feed.entries:
        pub = _parse_entry_date(entry)
        if pub and pub < since:
            continue

        title = (entry.get("title") or "").strip()
        # Source comes after the last " - " in Google News titles
        source_match = re.search(r" - ([^-]+)$", title)
        source = source_match.group(1).strip() if source_match else "Google News"
        clean_title = re.sub(r" - [^-]+$", "", title)

        items.append(
            {
                "title": clean_title,
                "source": source,
                "url": entry.get("link"),
                "published_at": pub.isoformat() if pub else None,
                "summary": (entry.get("summary") or "")[:400],
            }
        )

        if len(items) >= max_items:
            break

    return items
