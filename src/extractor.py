from __future__ import annotations

import re
from typing import Any

from .models import SearchQuery, VideoResult
from .utils import normalize_views, utc_now, video_id_from_url


class YouTubeExtractor:
    """All YouTube DOM selectors live here so they can be updated in one place."""

    RESULT = "ytd-video-renderer"
    METADATA = "#metadata-line span"

    @staticmethod
    def _is_published_text(text: str) -> bool:
        """Recognize visible publication/relative-date text, never inventing dates."""
        normalized = " ".join(text.lower().replace("\u00a0", " ").split())
        if re.fullmatch(r"(?:19|20)\d{2}", normalized):
            return True
        return bool(re.search(
            r"\b(hace|ago|streamed|premiered|published|publicado|emitido|estrenado|"
            r"en vivo|live|today|yesterday|hoy|ayer)\b",
            normalized,
        ))

    @staticmethod
    def _is_view_text(text: str) -> bool:
        normalized = " ".join(text.lower().replace("\u00a0", " ").split())
        if "view" in normalized or "vista" in normalized:
            return normalize_views(text) is not None
        # Bare counts are accepted only when their compact suffix makes their
        # meaning unambiguous in YouTube's metadata line (e.g. "103 k").
        return bool(re.fullmatch(
            r"\d+(?:[.,]\d+)?\s*(?:k|m|b|mil|millones?|thousand|million|billion)",
            normalized,
        ))

    @classmethod
    def classify_metadata(cls, metadata: list[str]) -> tuple[str, str]:
        """Return (views_text, published_text) from an unordered metadata list."""
        views_text = ""
        published_text = ""
        for text in metadata:
            visible = text.strip()
            if not visible:
                continue
            if not published_text and cls._is_published_text(visible):
                published_text = visible
            elif not views_text and cls._is_view_text(visible):
                views_text = visible
        return views_text, published_text

    @staticmethod
    def _text(node: Any, selector: str) -> str:
        try:
            return (node.locator(selector).first.text_content(timeout=2_000) or "").strip()
        except Exception:
            return ""

    @staticmethod
    def _attr(node: Any, selector: str, attribute: str) -> str:
        try:
            return (node.locator(selector).first.get_attribute(attribute, timeout=2_000) or "").strip()
        except Exception:
            return ""

    def extract(self, page: Any, search: SearchQuery, limit: int) -> list[VideoResult]:
        cards = page.locator(self.RESULT)
        cards.first.wait_for(state="attached", timeout=15_000)
        collected: list[VideoResult] = []
        seen_ids: set[str] = set()
        for index in range(cards.count()):
            card = cards.nth(index)
            href = self._attr(card, "a#video-title", "href")
            title = self._text(card, "a#video-title")
            video_id = video_id_from_url(href)
            if not video_id or not title or video_id in seen_ids:
                continue
            seen_ids.add(video_id)
            metadata = [text.strip() for text in card.locator(self.METADATA).all_text_contents() if text.strip()]
            views_text, published = self.classify_metadata(metadata)
            thumb = self._attr(card, "ytd-thumbnail img", "src") or self._attr(card, "ytd-thumbnail img", "data-thumb")
            collected.append(VideoResult(
                query=search.query, category=search.category, position=len(collected) + 1,
                video_id=video_id, title=title, channel=self._text(card, "ytd-channel-name #text"),
                views=normalize_views(views_text), views_text=views_text, published_text=published,
                duration=self._text(card, "ytd-thumbnail-overlay-time-status-renderer span"),
                video_url=f"https://www.youtube.com/watch?v={video_id}", thumbnail_url=thumb,
                scraped_at=utc_now(),
            ))
            if len(collected) >= limit:
                break
        return collected
