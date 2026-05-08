"""Fetch previous-day price action for a list of NSE tickers via yfinance.

Returns a dict per stock with: open, high, low, close, prev_close, change_pct,
volume, avg_volume_20d, volume_ratio, intraday_range_pct, gap_pct.
"""

from __future__ import annotations

import logging
from typing import Any

import yfinance as yf

log = logging.getLogger(__name__)


def fetch_prices(symbols: list[str]) -> dict[str, dict[str, Any]]:
    """Fetch ~30 days of daily bars and derive metrics for the most recent day.

    Args:
        symbols: NSE symbols WITHOUT exchange suffix, e.g. ["RELIANCE", "TCS"].

    Returns:
        Mapping of symbol -> metrics dict, or an error marker.
    """
    out: dict[str, dict[str, Any]] = {}
    yf_symbols = [f"{s}.NS" for s in symbols]

    try:
        # Group by ticker so we get one DataFrame per symbol; auto_adjust False
        # so 'Close' is the actual closing price (better for sanity-checking
        # against news headlines that reference unadjusted prices).
        data = yf.download(
            tickers=yf_symbols,
            period="40d",
            interval="1d",
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
        )
    except Exception as e:  # noqa: BLE001
        log.error("yfinance bulk download failed: %s", e)
        for s in symbols:
            out[s] = {"error": f"download_failed: {e}"}
        return out

    for sym, yf_sym in zip(symbols, yf_symbols, strict=True):
        try:
            # When only one ticker is requested yfinance returns a flat frame;
            # with many it returns a MultiIndex column frame.
            if len(yf_symbols) == 1:
                df = data
            else:
                df = data[yf_sym]

            df = df.dropna(how="all")
            if len(df) < 2:
                out[sym] = {"error": "insufficient_data"}
                continue

            last = df.iloc[-1]
            prev = df.iloc[-2]

            close = float(last["Close"])
            prev_close = float(prev["Close"])
            open_ = float(last["Open"])
            high = float(last["High"])
            low = float(last["Low"])
            volume = float(last["Volume"])
            avg_vol_20 = float(df["Volume"].tail(21).head(20).mean())

            change_pct = (close - prev_close) / prev_close * 100 if prev_close else 0.0
            gap_pct = (open_ - prev_close) / prev_close * 100 if prev_close else 0.0
            intraday_range_pct = (high - low) / prev_close * 100 if prev_close else 0.0
            volume_ratio = volume / avg_vol_20 if avg_vol_20 else 0.0

            out[sym] = {
                "date": str(df.index[-1].date()),
                "open": round(open_, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "prev_close": round(prev_close, 2),
                "change_pct": round(change_pct, 2),
                "gap_pct": round(gap_pct, 2),
                "intraday_range_pct": round(intraday_range_pct, 2),
                "volume": int(volume),
                "avg_volume_20d": int(avg_vol_20),
                "volume_ratio": round(volume_ratio, 2),
                # Sparkline data: last 30 closes
                "sparkline": [round(float(v), 2) for v in df["Close"].tail(30).tolist()],
            }
        except Exception as e:  # noqa: BLE001
            log.exception("Failed to parse data for %s", sym)
            out[sym] = {"error": f"parse_failed: {e}"}

    return out
