from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

from .browser import PlaywrightBrowser
from .config import Config
from .extractor import YouTubeExtractor
from .input_loader import load_queries
from .logger import configure_logger
from .storage import CsvStorage
from .utils import utc_now
from .validator import is_valid_result


def parse_args(argv: list[str] | None = None) -> Config:
    parser = argparse.ArgumentParser(description="Collect YouTube search results into resumable CSV files.")
    parser.add_argument("--input", required=True, type=Path, help="CSV containing a query column")
    parser.add_argument("--output", type=Path, default=Path("output"))
    parser.add_argument("--limit", type=int, default=10, help="maximum videos per query")
    parser.add_argument("--queries", type=int, help="process only the first N input rows")
    parser.add_argument("--resume", action="store_true", help="skip successfully checkpointed queries")
    parser.add_argument("--headless", action="store_true", help="run Chromium without a visible window")
    parser.add_argument("--delay-min", type=float, default=2.0)
    parser.add_argument("--delay-max", type=float, default=5.0)
    parser.add_argument("--retries", type=int, default=2, help="retries after the first attempt")
    args = parser.parse_args(argv)
    return Config(args.input, args.output, args.limit, args.queries, args.resume, args.headless,
                  args.delay_min, args.delay_max, args.retries)


def run(config: Config) -> int:
    searches = load_queries(config.input_path)
    if config.query_limit:
        searches = searches[:config.query_limit]
    storage = CsvStorage(config.output_dir)
    logger = configure_logger(Path("logs"))
    started_at = utc_now()
    completed = failed = videos = 0
    extractor = YouTubeExtractor()
    total = len(searches)

    with PlaywrightBrowser(config.headless, config.navigation_timeout_ms) as browser:
        for number, search in enumerate(searches, start=1):
            if config.resume and storage.is_completed(search):
                print(f"[{number:03}/{total}] {search.query}\n    - already completed; skipped")
                continue
            print(f"[{number:03}/{total}] {search.query}")
            for attempt in range(config.retries + 1):
                try:
                    page = browser.navigate(search.url)
                    results = [result for result in extractor.extract(page, search, config.result_limit) if is_valid_result(result)]
                    videos += storage.save_results(results)
                    storage.mark_completed(search)
                    completed += 1
                    print(f"    OK {len(results)} videos")
                    break
                except Exception as error:
                    if attempt < config.retries:
                        print(f"    WARNING {type(error).__name__}; retry {attempt + 1}/{config.retries}")
                        logger.warning("Query %r attempt %d failed: %s", search.query, attempt + 1, error)
                        continue
                    failed += 1
                    storage.save_error(search, error, utc_now(), attempt)
                    logger.exception("Query %r failed after %d retries", search.query, config.retries)
                    print(f"    FAILED: {error}")
            if number < total:
                time.sleep(random.uniform(config.delay_min, config.delay_max))

    storage.write_summary({
        "started_at": started_at, "finished_at": utc_now(), "total_queries": total,
        "completed_queries": completed, "failed_queries": failed, "videos_collected": videos,
        "requested_results_per_query": config.result_limit,
    })
    return 0


def main() -> None:
    try:
        raise SystemExit(run(parse_args()))
    except (ValueError, FileNotFoundError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
