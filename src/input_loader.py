from __future__ import annotations

import csv
from pathlib import Path

from .models import SearchQuery
from .utils import youtube_search_url


def load_queries(path: Path) -> list[SearchQuery]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "query" not in reader.fieldnames:
            raise ValueError("Input CSV must contain a 'query' column")
        queries = []
        for line, row in enumerate(reader, start=2):
            query = (row.get("query") or "").strip()
            if not query:
                raise ValueError(f"Input CSV row {line} has an empty query")
            url = (row.get("url") or "").strip() or youtube_search_url(query)
            queries.append(SearchQuery(query=query, category=(row.get("category") or "").strip(), url=url))
    return queries
