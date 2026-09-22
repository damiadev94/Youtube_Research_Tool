from __future__ import annotations

from .models import VideoResult


def is_valid_result(result: VideoResult) -> bool:
    return bool(result.query and result.position > 0 and result.title and result.video_url)
