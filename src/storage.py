from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .models import SearchQuery, VideoResult


RESULT_COLUMNS = [
    "query",
    "category",
    "position",
    "video_id",
    "title",
    "channel",
    "views",
    "views_text",
    "published_text",
    "duration",
    "video_url",
    "thumbnail_url",
    "scraped_at",
]

ERROR_COLUMNS = [
    "query",
    "category",
    "error_type",
    "error_message",
    "timestamp",
    "retry_count",
]


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
        self._completed_keys = self._load_checkpoints()

    @staticmethod
    def _ensure_headers(path: Path, columns: list[str]) -> None:
        if not path.exists() or path.stat().st_size == 0:
            with path.open("w", encoding="utf-8", newline="") as handle:
                csv.DictWriter(
                    handle,
                    fieldnames=columns,
                ).writeheader()

    def _load_result_keys(self) -> set[tuple[str, str, str]]:
        """
        Load existing result identities.

        A result is uniquely identified by:
            query + category + video_id

        The video_id alone is intentionally NOT enough because the same
        video can legitimately appear in multiple search queries.
        """
        if not self.results_path.exists():
            return set()

        with self.results_path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as handle:
            return {
                (
                    row.get("query", ""),
                    row.get("category", ""),
                    row.get("video_id", ""),
                )
                for row in csv.DictReader(handle)
                if row.get("query")
                and row.get("category")
                and row.get("video_id")
            }

    def _load_checkpoints(self) -> set[str]:
        """
        Load successfully completed searches.

        A checkpoint is created only after the query has been successfully
        extracted and its results persisted.
        """
        if not self.checkpoint_path.exists():
            return set()

        try:
            payload = json.loads(
                self.checkpoint_path.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            return set()

        completed = payload.get("completed", [])

        if not isinstance(completed, list):
            return set()

        return {
            str(item)
            for item in completed
            if item
        }

    @staticmethod
    def key(search: SearchQuery) -> str:
        """
        Stable identity for a search query.

        Includes URL so that two otherwise identical queries pointing to
        different search URLs remain distinguishable.
        """
        return f"{search.category}\u001f{search.query}\u001f{search.url}"

    def is_completed(self, search: SearchQuery) -> bool:
        return self.key(search) in self._completed_keys

    def save_results(self, results: Iterable[VideoResult]) -> int:
        """
        Persist results idempotently.

        Existing results are not duplicated.

        Important:
        - Same video in different queries is allowed.
        - Same video in the same query/category is stored only once.
        """
        rows: list[dict] = []

        for result in results:
            if not result.video_id:
                continue

            key = (
                result.query,
                result.category,
                result.video_id,
            )

            if key in self._result_keys:
                continue

            self._result_keys.add(key)
            rows.append(result.__dict__)

        if rows:
            with self.results_path.open(
                "a",
                encoding="utf-8",
                newline="",
            ) as handle:
                csv.DictWriter(
                    handle,
                    fieldnames=RESULT_COLUMNS,
                ).writerows(rows)

        return len(rows)

    def mark_completed(self, search: SearchQuery) -> None:
        """
        Mark a search as successfully completed.

        The checkpoint is written only after save_results() has succeeded.
        """
        key = self.key(search)

        if key in self._completed_keys:
            return

        self._completed_keys.add(key)

        self.checkpoint_path.write_text(
            json.dumps(
                {
                    "completed": sorted(self._completed_keys),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def save_error(
        self,
        search: SearchQuery,
        error: Exception,
        timestamp: str,
        retry_count: int,
    ) -> None:
        with self.errors_path.open(
            "a",
            encoding="utf-8",
            newline="",
        ) as handle:
            csv.DictWriter(
                handle,
                fieldnames=ERROR_COLUMNS,
            ).writerow(
                {
                    "query": search.query,
                    "category": search.category,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "timestamp": timestamp,
                    "retry_count": retry_count,
                }
            )

    def write_summary(self, summary: dict) -> None:
        self.summary_path.write_text(
            json.dumps(
                summary,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )