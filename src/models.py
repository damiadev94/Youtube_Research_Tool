from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SearchQuery:
    query: str
    category: str = ""
    url: str = ""


@dataclass(frozen=True)
class VideoResult:
    query: str
    category: str
    position: int
    video_id: str
    title: str
    channel: str
    views: Optional[int]
    views_text: str
    published_text: str
    duration: str
    video_url: str
    thumbnail_url: str
    scraped_at: str
