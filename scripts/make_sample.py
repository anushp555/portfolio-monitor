"""Generate a sample report from the actual portfolio.yaml.

Synthesizes plausible price action, catalysts, and analyses for every stock
in portfolio.yaml. Useful for:
  - Local frontend dev without burning Gemini calls
  - Testing the dashboard before you have a GEMINI_API_KEY
  - CI smoke tests
"""

from __future__ import annotations

import datetime as dt
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from collectors.common import load_portfolio  # noqa: E402

REPORTS_DIR = ROOT / "reports"


# A library of plausible catalyst seeds keyed by sector. Picked at random.
SECTOR_CATALYSTS = {
    "Banking": [
        ("Result", "Q4 results: NII up 12% YoY, NIM at 4.1%", "Result released after market hours"),
        ("Updates", "RBI approves additional branch licences", None),
        ("Updates", "Asset quality stable; gross NPA at 2.1%", None),
    ],
    "NBFC": [
        ("Result", "Q4 PAT up 18% YoY on AUM expansion", None),
        ("Updates", "Co-lending arrangement signed with HDFC Bank", None),
    ],
    "Power": [
        ("Updates", "₹1,800 cr solar EPC contract awarded", None),
        ("Result", "Q4 EBITDA margin expansion driven by lower coal costs", None),
    ],
    "Renewable Energy": [
        ("Updates", "Order book crosses ₹4,500 cr after fresh wind tenders", None),
        ("Updates", "Repowering project commissioned in Tamil Nadu", None),
    ],
    "Renewable Energy Finance": [
        ("Updates", "Loan book grows 28% YoY; new disbursements ₹4,200 cr", None),
    ],
    "Solar EPC": [
        ("Updates", "Wins ₹2,100 cr Adani Green order; execution by FY27", None),
    ],
    "Heavy Electrical Equipment": [
        ("Updates", "Bags ₹390 cr transformer order from PowerGrid", None),
    ],
    "Commercial Vehicles": [
        ("Updates", "October CV wholesales up 9% YoY; M&HCV strong", None),
    ],
    "Passenger Vehicles": [
        ("Result", "Q3 standalone PAT loss; JLR retail volumes -14% YoY", None),
        ("Updates", "Sierra.ev launch announced for Mar-2026 delivery", None),
    ],
    "FMCG": [
        ("Updates", "GST Council raises cess on cigarettes by 3pp", None),
    ],
    "Hospitality": [
        ("Updates", "RevPAR up 11% YoY; festive bookings strong", None),
        ("Updates", "Two new properties signed in Tier-2 markets", None),
    ],
    "Plastics / Pipes": [
        ("Updates", "PVC resin spreads compress; FY27 margin guidance cut", None),
    ],
    "Insurance": [
        ("Result", "Q4 VNB margin at 26.2%; APE up 14% YoY", None),
        ("Updates", "Board approves preferential issue to anchor investors", None),
    ],
    "Electronics Refurbishing": [
        ("Updates", "Microsoft authorized refurbisher status renewed", None),
    ],
}


def _sparkline(base: float, days: int = 30, drift: float = 0.0) -> list[float]:
    out = []
    px = base * (1 - drift)
    for _ in range(days):
        px *= 1 + random.uniform(-0.018, 0.018)
        out.append(round(px, 2))
    return out


def _synth_catalysts(sector: str | None) -> list[dict]:
    """Return 0–3 plausible BSE-shaped announcements for the sector."""
    pool = SECTOR_CATALYSTS.get(sector or "", [])
    if not pool:
        return []
    n = random.choices([0, 1, 2], weights=[3, 4, 2])[0]
    return [
        {
            "headline": h,
            "category": cat,
            "more_info": more,
            "attached_at": (dt.datetime(2026, 4, 28, random.randint(9, 18),
                                        random.randint(0, 59))).isoformat(sep=" "),
            "pdf_url": None,
            "source": "BSE",
        }
        for cat, h, more in random.sample(pool, k=min(n, len(pool)))
    ]


def _synth_news(name: str, headlines_pool: list) -> list[dict]:
    if not headlines_pool:
        return []
    n = random.choices([0, 1, 2, 3], weights=[2, 3, 3, 2])[0]
    sources = ["Moneycontrol", "Economic Times", "Mint", "Business Standard", "CNBC TV18"]
    items = []
    for h in random.sample(headlines_pool, k=min(n, len(headlines_pool))):
        items.append({
            "title": h,
            "source": random.choice(sources),
            "published_at": dt.datetime(2026, 4, 28,
                                        random.randint(8, 17),
                                        random.randint(0, 59),
                                        tzinfo=dt.timezone.utc).isoformat(),
            "summary": f"{name} — {h[:120]}.",
        })
    return items


SECTOR_NEWS = {
    "Banking": [
        "Indian banks see deposit growth pick up in March quarter",
        "RBI maintains repo at 6.50%; banking pack reacts mildly",
    ],
    "Power": [
        "Power demand hits new peak amid early heatwave",
    ],
    "Renewable Energy": [
        "Solar tender pipeline at record high, says MNRE",
    ],
    "FMCG": [
        "Cigarette stocks under pressure on tax hike rumours",
    ],
    "Hospitality": [
        "Hotel ARRs hit decade high in March quarter",
    ],
    "Passenger Vehicles": [
        "Auto industry sees double-digit growth in March",
    ],
    "Commercial Vehicles": [
        "M&HCV demand recovering on infra push",
    ],
    "Insurance": [
        "Life insurance APE growth normalises; H2 outlook positive",
    ],
}


def _classification_for(change_pct: float, vol_ratio: float, has_catalyst: bool) -> tuple:
    abs_chg = abs(change_pct)
    if abs_chg >= 2.0 and has_catalyst:
        return "catalyst_drove_move", "high"
    if abs_chg >= 2.0 and not has_catalyst and vol_ratio >= 1.4:
        return "move_without_catalyst", "medium"
    if has_catalyst and abs_chg < 0.6:
        return "catalyst_without_move", "medium"
    return "no_signal", "high"


def make_sample() -> dict:
    today = dt.date(2026, 4, 29)
    prev = dt.date(2026, 4, 28)

    portfolio = load_portfolio()

    out_stocks = []
    for stock in portfolio:
        symbol = stock["symbol"]
        sector = stock.get("sector")
        skip = bool(stock.get("skip_catalysts", False))

        # Plausible price for sample purposes; real run will use yfinance
        base_price = round(random.uniform(120, 3500), 2)
        change_pct = round(random.gauss(0, 1.6), 2)
        if random.random() < 0.18:  # ~18% of the time, an outsized move
            change_pct = round(random.choice([-1, 1]) * random.uniform(2.5, 5.0), 2)
        prev_close = round(base_price / (1 + change_pct / 100), 2)
        vol_ratio = round(max(0.4, random.gauss(1.05, 0.45)), 2)

        sp = _sparkline(base_price, drift=0.06)
        sp[-1] = base_price

        if skip:
            analysis = {
                "classification": "price_only",
                "primary_catalyst": None,
                "analysis": "Price-tracking instrument (SGB/ETF). No catalyst correlation performed.",
                "confidence": "high",
                "flags": [],
            }
            bse_anns: list = []
            news_items: list = []
        else:
            bse_anns = _synth_catalysts(sector)
            news_items = _synth_news(stock["name"], SECTOR_NEWS.get(sector or "", []))
            has_cat = bool(bse_anns or news_items)

            classification, confidence = _classification_for(
                change_pct, vol_ratio, has_cat
            )

            flags = []
            if classification == "move_without_catalyst" and vol_ratio >= 1.5:
                flags.append("POSSIBLE_LEAK_OR_FLOW")

            primary = bse_anns[0]["headline"] if bse_anns else (
                news_items[0]["title"] if news_items else None
            )

            analysis_text_map = {
                "catalyst_drove_move": (
                    f"{symbol} moved {change_pct:+.2f}% on {vol_ratio:.1f}x volume "
                    f"with a clear catalyst on the tape. Move and disclosure align."
                ),
                "move_without_catalyst": (
                    f"{symbol} moved {change_pct:+.2f}% on elevated {vol_ratio:.1f}x "
                    f"volume with no obvious catalyst. Worth monitoring for delayed disclosure."
                ),
                "catalyst_without_move": (
                    f"{symbol} disclosed material news but the stock barely budged "
                    f"({change_pct:+.2f}%). Possible lag setup if details prove accretive."
                ),
                "no_signal": (
                    f"{symbol} closed {change_pct:+.2f}% on {vol_ratio:.1f}x volume "
                    f"with no material catalysts. Quiet day."
                ),
            }

            analysis = {
                "classification": classification,
                "primary_catalyst": primary,
                "analysis": analysis_text_map[classification],
                "confidence": confidence,
                "flags": flags,
            }

        out_stocks.append({
            "symbol": symbol,
            "name": stock["name"],
            "sector": sector,
            "notes": stock.get("notes"),
            "skip_catalysts": skip,
            "price_action": {
                "date": prev.isoformat(),
                "open": round(prev_close * (1 + random.uniform(-0.005, 0.005)), 2),
                "high": round(base_price * (1 + random.uniform(0.001, 0.012)), 2),
                "low": round(base_price * (1 - random.uniform(0.001, 0.012)), 2),
                "close": base_price,
                "prev_close": prev_close,
                "change_pct": change_pct,
                "gap_pct": round(random.uniform(-0.4, 0.4), 2),
                "intraday_range_pct": round(abs(change_pct) + random.uniform(0.4, 1.2), 2),
                "volume": int(random.uniform(5e5, 5e7) * vol_ratio),
                "avg_volume_20d": int(random.uniform(5e5, 5e7)),
                "volume_ratio": vol_ratio,
                "sparkline": sp,
            },
            "bse_announcements": bse_anns,
            "nse_announcements": [],
            "news": news_items,
            "events": [],
            "sebi_mentions": [],
            "analysis": analysis,
        })

    return {
        "report_date": today.isoformat(),
        "trading_day": prev.isoformat(),
        "generated_at": dt.datetime(2026, 4, 29, 8, 30).isoformat(),
        "stocks": out_stocks,
    }


def main() -> None:
    random.seed(99)  # deterministic; this seed produces all 5 classification states
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report = make_sample()
    out = REPORTS_DIR / "sample.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    (REPORTS_DIR / "latest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    (REPORTS_DIR / f"{report['report_date']}.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False)
    )
    (REPORTS_DIR / "index.json").write_text(json.dumps({
        "reports": [report["report_date"]],
        "updated_at": report["generated_at"],
    }, indent=2))

    # Quick summary
    counts: dict[str, int] = {}
    for s in report["stocks"]:
        c = s["analysis"]["classification"]
        counts[c] = counts.get(c, 0) + 1
    print(f"Wrote sample report with {len(report['stocks'])} stocks: {counts}")
    print(f"Path: {out}")


if __name__ == "__main__":
    main()
