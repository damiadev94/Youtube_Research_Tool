from __future__ import annotations

from typing import Any

from .models import SearchQuery, VideoResult
from .utils import normalize_views, utc_now, video_id_from_url


class YouTubeExtractor:
    """All YouTube DOM selectors live here so they can be updated in one place."""

    RESULT = "ytd-video-renderer"

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
            metadata = [text.strip() for text in card.locator("#metadata-line span").all_text_contents() if text.strip()]
            views_text = next((item for item in metadata if "view" in item.lower() or "vista" in item.lower()), "")
            published = next((item for item in metadata if item != views_text), "")
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
