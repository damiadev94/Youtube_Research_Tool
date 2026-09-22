from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .models import SearchQuery, VideoResult

RESULT_COLUMNS = ["query", "category", "position", "video_id", "title", "channel", "views", "views_text", "published_text", "duration", "video_url", "thumbnail_url", "scraped_at"]
ERROR_COLUMNS = ["query", "category", "error_type", "error_message", "timestamp", "retry_count"]


class CsvStorage:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.results_path = output_dir / "results.csv"
        self.errors_path = output_dir / "errors.csv"
        self.checkpoint_path = output_dir / "checkpoints.json"
        self.summary_path = output_dir / "run_summary.json"
        output_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_headers(self.results_path, RESULT_COLUMNS)
        self._ensure_headers(self.errors_path, ERROR_COLUMNS)
        self._result_keys = self._load_result_keys()

    @staticmethod
    def _ensure_headers(path: Path, columns: list[str]) -> None:
        if not path.exists() or path.stat().st_size == 0:
            with path.open("w", encoding="utf-8", newline="") as handle:
                csv.DictWriter(handle, fieldnames=columns).writeheader()

    def _load_result_keys(self) -> set[tuple[str, str, str]]:
        with self.results_path.open("r", encoding="utf-8", newline="") as handle:
            return {(row["query"], row["category"], row["video_id"])
                    for row in csv.DictReader(handle) if row.get("video_id")}

    def _checkpoints(self) -> set[str]:
        if not self.checkpoint_path.exists():
            return set()
        return set(json.loads(self.checkpoint_path.read_text(encoding="utf-8")).get("completed", []))

    @staticmethod
    def key(search: SearchQuery) -> str:
        return f"{search.category}\u001f{search.query}\u001f{search.url}"

    def is_completed(self, search: SearchQuery) -> bool:
        return self.key(search) in self._checkpoints()

    def save_results(self, results: Iterable[VideoResult]) -> int:
        rows = []
        for result in results:
            key = (result.query, result.category, result.video_id)
            if key not in self._result_keys:
                self._result_keys.add(key)
                rows.append(result.__dict__)
        if rows:
            with self.results_path.open("a", encoding="utf-8", newline="") as handle:
                csv.DictWriter(handle, fieldnames=RESULT_COLUMNS).writerows(rows)
        return len(rows)

    def mark_completed(self, search: SearchQuery) -> None:
        completed = self._checkpoints()
        completed.add(self.key(search))
        self.checkpoint_path.write_text(json.dumps({"completed": sorted(completed)}, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_error(self, search: SearchQuery, error: Exception, timestamp: str, retry_count: int) -> None:
        with self.errors_path.open("a", encoding="utf-8", newline="") as handle:
            csv.DictWriter(handle, fieldnames=ERROR_COLUMNS).writerow({
                "query": search.query, "category": search.category, "error_type": type(error).__name__,
                "error_message": str(error), "timestamp": timestamp, "retry_count": retry_count,
            })

    def write_summary(self, summary: dict) -> None:
        self.summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
