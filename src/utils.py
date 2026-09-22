from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, quote_plus, urlparse


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def youtube_search_url(query: str) -> str:
    return f"https://www.youtube.com/results?search_query={quote_plus(query)}"


def video_id_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.path == "/watch":
        return parse_qs(parsed.query).get("v", [""])[0]
    if parsed.netloc.endswith("youtu.be"):
        return parsed.path.strip("/").split("/")[0]
    if parsed.path.startswith("/shorts/"):
        return parsed.path.split("/")[2] if len(parsed.path.split("/")) > 2 else ""
    return ""


def normalize_views(text: str) -> int | None:
    """Convert common YouTube view counts; return None for ambiguous text."""
    cleaned = " ".join((text or "").lower().replace("\u00a0", " ").split())
    if not cleaned:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*([kmb]|mil|millones?|thousand|million|billion)?\s*(?:views?|vistas?)\b", cleaned)
    if not match:
        return None
    number_text, suffix = match.groups()
    suffix = suffix or ""
    # A lone separator in a four+ digit count is normally a thousands separator.
    if not suffix and re.fullmatch(r"\d{1,3}[.,]\d{3}", number_text):
        return int(number_text.replace(".", "").replace(",", ""))
    number = float(number_text.replace(",", "."))
    multipliers = {"k": 1_000, "mil": 1_000, "thousand": 1_000,
                   "m": 1_000_000, "million": 1_000_000, "millions": 1_000_000,
                   "b": 1_000_000_000, "billion": 1_000_000_000}
    return int(number * multipliers.get(suffix, 1))
