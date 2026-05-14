"""LLM correlation: feeds catalysts + price action to Groq, returns analysis JSON.

Uses Groq's free-tier API with the Llama 3.3 70B Versatile model. Free tier
limits (as of 2026): 30 RPM, 14,400 RPD, 30,000 TPM. More than enough headroom
for a 20-stock portfolio.

Env var: GROQ_API_KEY  (get a free key at https://console.groq.com/keys)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

from groq import Groq

from .prompts import SYSTEM_PROMPT, build_user_prompt

log = logging.getLogger(__name__)

MODEL_NAME = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
RPM_LIMIT = 25  # safely under Groq's 30 RPM free-tier ceiling
_last_call_ts = 0.0
_client: "Groq | None" = None


def _get_client() -> "Groq":
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY env var is required")
    _client = Groq(api_key=api_key)
    return _client


def _throttle() -> None:
    global _last_call_ts
    min_interval = 60.0 / RPM_LIMIT
    elapsed = time.time() - _last_call_ts
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _last_call_ts = time.time()


def _strip_fences(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def analyze_stock(stock_payload: dict[str, Any]) -> dict[str, Any]:
    """Run the LLM correlation step. Returns parsed dict; on failure, a
    deterministic fallback so the dashboard always has something to show.
    """
    fallback: dict[str, Any] = {
        "classification": "no_signal",
        "primary_catalyst": None,
        "analysis": "Automated analysis unavailable; review raw catalysts below.",
        "confidence": "low",
        "flags": [],
    }

    try:
        client = _get_client()
    except Exception as e:  # noqa: BLE001
        log.error("Groq client init failed: %s", e)
        return fallback

    prompt = build_user_prompt(stock_payload)

    last_err: Exception | None = None
    for attempt in range(4):
        try:
            _throttle()
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=600,
                response_format={"type": "json_object"},
            )
            text = _strip_fences(resp.choices[0].message.content or "")
            parsed = json.loads(text)
            for k, v in fallback.items():
                parsed.setdefault(k, v)
            return parsed
        except Exception as e:  # noqa: BLE001
            last_err = e
            log.warning("Groq call failed (attempt %d): %s", attempt + 1, e)
            time.sleep(2 ** attempt)

    log.error("All Groq retries failed: %s", last_err)
    return fallback
