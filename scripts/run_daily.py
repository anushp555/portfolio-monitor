"""Daily orchestrator.

Steps:
  1. Load portfolio.yaml
  2. Determine the previous trading day
  3. In parallel: fetch prices, BSE announcements, NSE announcements, news,
     events, SEBI mentions
  4. For each stock, build a payload and call the LLM correlator
  5. Write reports/YYYY-MM-DD.json + reports/latest.json
  6. Maintain reports/index.json listing all available report dates

Run locally:
    GEMINI_API_KEY=... python -m scripts.run_daily
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
import sys
from pathlib import Path
from typing import Any

import httpx

# Add project root to path so `python -m scripts.run_daily` works from anywhere
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.correlator import analyze_stock  # noqa: E402
from collectors.bse_announcements import fetch_bse_announcements  # noqa: E402
from collectors.common import iso, load_portfolio, now_ist, previous_trading_day  # noqa: E402
from collectors.earnings import fetch_events  # noqa: E402
from collectors.news import fetch_news  # noqa: E402
from collectors.nse_announcements import fetch_nse_announcements  # noqa: E402
from collectors.prices import fetch_prices  # noqa: E402
from collectors.sebi import fetch_sebi_mentions  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("orchestrator")

REPORTS_DIR = ROOT / "reports"


async def _gather_one_stock(
    client: httpx.AsyncClient,
    stock: dict[str, Any],
    prev_day: dt.date,
    today: dt.date,
    sebi_hits: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Pull all per-stock catalysts in parallel.

    If stock['skip_catalysts'] is True (e.g. SGBs, ETFs), we don't fetch any
    catalysts. The price collector still runs upstream.
    """
    symbol = stock["symbol"]
    name = stock["name"]
    bse_code = stock.get("bse_code")
    skip = bool(stock.get("skip_catalysts", False))

    if skip:
        return {
            "symbol": symbol,
            "name": name,
            "sector": stock.get("sector"),
            "notes": stock.get("notes"),
            "skip_catalysts": True,
            "bse_announcements": [],
            "nse_announcements": [],
            "news": [],
            "events": [],
            "sebi_mentions": [],
        }

    # 24h news lookback from start of prev_day in UTC
    since = dt.datetime.combine(prev_day, dt.time.min, tzinfo=dt.timezone.utc)

    bse_task = (
        fetch_bse_announcements(client, bse_code, prev_day, today)
        if bse_code
        else asyncio.sleep(0, result=[])
    )
    nse_task = fetch_nse_announcements(client, symbol, prev_day, today)
    news_task = fetch_news(client, name, symbol, since)
    events_task = fetch_events(client, symbol)

    bse_anns, nse_anns, news_items, events = await asyncio.gather(
        bse_task, nse_task, news_task, events_task, return_exceptions=False
    )

    return {
        "symbol": symbol,
        "name": name,
        "sector": stock.get("sector"),
        "notes": stock.get("notes"),
        "skip_catalysts": False,
        "bse_announcements": bse_anns,
        "nse_announcements": nse_anns,
        "news": news_items,
        "events": events,
        "sebi_mentions": sebi_hits.get(name, []),
    }


async def collect_all(stocks: list[dict[str, Any]], prev_day: dt.date) -> dict[str, Any]:
    # Prices: synchronous library, run once for all symbols
    log.info("Fetching prices for %d symbols", len(stocks))
    prices = fetch_prices([s["symbol"] for s in stocks])

    # Derive the actual trading day from yfinance data (more reliable than calendar)
    from collectors.common import derive_trading_day
    actual_trading_day = derive_trading_day(prices)
    if actual_trading_day and actual_trading_day != prev_day:
        log.info(
            "Adjusting trading day: calendar said %s, yfinance data says %s",
            prev_day, actual_trading_day,
        )
        prev_day = actual_trading_day
    today = prev_day + dt.timedelta(days=1)
    log.info("Using trading day: %s for catalyst lookback", prev_day)

    async with httpx.AsyncClient(http2=False, follow_redirects=True) as client:
        log.info("Fetching SEBI press mentions")
        sebi_hits = await fetch_sebi_mentions(client, [s["name"] for s in stocks])

        log.info("Fetching per-stock catalysts in parallel")
        tasks = [
            _gather_one_stock(client, s, prev_day, today, sebi_hits) for s in stocks
        ]
        per_stock = await asyncio.gather(*tasks)

    # Combine prices + catalysts
    for entry in per_stock:
        entry["price_action"] = prices.get(entry["symbol"], {"error": "no_price_data"})

    return {
        "report_date": iso(today),
        "trading_day": iso(prev_day),
        "generated_at": iso(now_ist()),
        "stocks": per_stock,
    }

    async with httpx.AsyncClient(http2=False, follow_redirects=True) as client:
        log.info("Fetching SEBI press mentions")
        sebi_hits = await fetch_sebi_mentions(client, [s["name"] for s in stocks])

        log.info("Fetching per-stock catalysts in parallel")
        tasks = [
            _gather_one_stock(client, s, prev_day, today, sebi_hits) for s in stocks
        ]
        per_stock = await asyncio.gather(*tasks)

    # Combine prices + catalysts
    for entry in per_stock:
        entry["price_action"] = prices.get(entry["symbol"], {"error": "no_price_data"})

    return {
        "report_date": iso(today),
        "trading_day": iso(prev_day),
        "generated_at": iso(now_ist()),
        "stocks": per_stock,
    }


def _summarize_for_llm(entry: dict[str, Any]) -> dict[str, Any]:
    """Trim fields the LLM doesn't need (sparkline arrays, raw HTML, etc.)."""
    pa = entry.get("price_action", {}) or {}
    pa_slim = {k: v for k, v in pa.items() if k != "sparkline"}
    return {
        "symbol": entry["symbol"],
        "name": entry["name"],
        "sector": entry.get("sector"),
        "price_action": pa_slim,
        "bse_announcements": [
            {k: a.get(k) for k in ("headline", "category", "subcategory", "more_info", "attached_at")}
            for a in entry.get("bse_announcements", [])[:6]
        ],
        "nse_announcements": [
            {k: a.get(k) for k in ("headline", "category", "more_info", "attached_at")}
            for a in entry.get("nse_announcements", [])[:6]
        ],
        "news": [
            {k: n.get(k) for k in ("title", "source", "published_at", "summary")}
            for n in entry.get("news", [])[:8]
        ],
        "events": entry.get("events", [])[:4],
        "sebi_mentions": [
            {k: s.get(k) for k in ("title", "published_at")}
            for s in entry.get("sebi_mentions", [])
        ],
    }


def run_analysis(report: dict[str, Any]) -> dict[str, Any]:
    log.info("Running LLM correlation for %d stocks", len(report["stocks"]))
    for entry in report["stocks"]:
        if entry.get("skip_catalysts"):
            entry["analysis"] = {
                "classification": "price_only",
                "primary_catalyst": None,
                "analysis": "Price-tracking instrument (SGB/ETF). No catalyst correlation performed.",
                "confidence": "high",
                "flags": [],
            }
            log.info("  %s -> price_only (catalysts skipped)", entry["symbol"])
            continue
        slim = _summarize_for_llm(entry)
        result = analyze_stock(slim)
        entry["analysis"] = result
        log.info(
            "  %s -> %s (%s confidence)",
            entry["symbol"],
            result.get("classification"),
            result.get("confidence"),
        )
    return report


def write_outputs(report: dict[str, Any]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = report["report_date"]

    daily_path = REPORTS_DIR / f"{date_str}.json"
    daily_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    log.info("Wrote %s", daily_path)

    latest_path = REPORTS_DIR / "latest.json"
    latest_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    # Index of all reports
    existing = sorted(p.stem for p in REPORTS_DIR.glob("*.json") if p.stem not in {"latest", "index"})
    index = {"reports": existing, "updated_at": report["generated_at"]}
    (REPORTS_DIR / "index.json").write_text(json.dumps(index, indent=2))
    log.info("Wrote index with %d entries", len(existing))


async def main() -> None:
    stocks = load_portfolio()
    if not stocks:
        log.error("No stocks in portfolio.yaml")
        sys.exit(1)

    prev_day = previous_trading_day()
    log.info("Building report for trading day: %s", prev_day)

    report = await collect_all(stocks, prev_day)
    report = run_analysis(report)
    write_outputs(report)

    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
