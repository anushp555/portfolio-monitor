"""LLM correlation: feeds catalysts + price action to Gemini, returns analysis JSON.

Uses the modern `google-genai` SDK. Free tier on `gemini-2.0-flash` is
generous (15 RPM, 1500 RPD at the time this was written) — comfortably more
than a 5-50 stock portfolio needs.

Env var: GEMINI_API_KEY  (get a free key at https://aistudio.google.com/apikey)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

from google import genai
from google.genai import types

from .prompts import SYSTEM_PROMPT, build_user_prompt

log = logging.getLogger(__name__)

MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
RPM_LIMIT = 6  # gemini-2.5-flash-lite free tier is 10 RPM; stay well under
_last_call_ts = 0.0
_client: "genai.Client | None" = None


def _get_client() -> "genai.Client":
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY env var is required")
    _client = genai.Client(api_key=api_key)
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
    """Run the LLM correlation step. Returns a parsed dict; on failure, a
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
        log.error("Gemini client init failed: %s", e)
        return fallback

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.2,
        response_mime_type="application/json",
    )
    prompt = build_user_prompt(stock_payload)

    last_err: Exception | None = None
    for attempt in range(3):
        try:
            _throttle()
            resp = client.models.generate_content(
                model=MODEL_NAME, contents=prompt, config=config
            )
            text = _strip_fences(resp.text or "")
            parsed = json.loads(text)
            for k, v in fallback.items():
                parsed.setdefault(k, v)
            return parsed
        except Exception as e:  # noqa: BLE001
            last_err = e
            log.warning("Gemini call failed (attempt %d): %s", attempt + 1, e)
            time.sleep(2 ** attempt)

    log.error("All Gemini retries failed: %s", last_err)
    return fallback
