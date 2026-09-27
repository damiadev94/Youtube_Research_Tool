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
    parser = argparse.ArgumentParser(
        description="Collect YouTube search results into resumable CSV files."
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="CSV containing a query column",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="maximum videos per query",
    )

    parser.add_argument(
        "--queries",
        type=int,
        help="process only N input rows starting at --start",
    )

    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="1-based input row from which processing starts",
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="skip successfully checkpointed queries",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="run Chromium without a visible window",
    )

    parser.add_argument(
        "--delay-min",
        type=float,
        default=2.0,
    )

    parser.add_argument(
        "--delay-max",
        type=float,
        default=5.0,
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="retries after the first attempt",
    )

    args = parser.parse_args(argv)

    if args.start < 1:
        parser.error("--start must be >= 1")

    if args.queries is not None and args.queries < 1:
        parser.error("--queries must be >= 1")

    if args.limit < 1:
        parser.error("--limit must be >= 1")

    if args.delay_min < 0 or args.delay_max < 0:
        parser.error("--delay-min and --delay-max must be >= 0")

    if args.delay_min > args.delay_max:
        parser.error("--delay-min cannot be greater than --delay-max")

    if args.retries < 0:
        parser.error("--retries must be >= 0")

    return Config(
        input_path=args.input,
        output_dir=args.output,
        result_limit=args.limit,
        query_limit=args.queries,
        resume=args.resume,
        headless=args.headless,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        retries=args.retries,
        navigation_timeout_ms=30_000,
        start=args.start,
    )


def run(config: Config) -> int:
    searches = load_queries(config.input_path)

    total_input_queries = len(searches)

    start_index = config.start - 1

    if start_index >= total_input_queries:
        raise ValueError(
            f"--start {config.start} is beyond the input "
            f"({total_input_queries} queries available)"
        )

    # Keep only the queries starting from --start.
    searches = searches[start_index:]

    # Then apply --queries to that slice.
    if config.query_limit is not None:
        searches = searches[: config.query_limit]

    storage = CsvStorage(config.output_dir)
    logger = configure_logger(Path("logs"))

    started_at = utc_now()

    completed = 0
    failed = 0
    skipped = 0
    videos = 0

    extractor = YouTubeExtractor()

    total = len(searches)

    with PlaywrightBrowser(
        config.headless,
        config.navigation_timeout_ms,
    ) as browser:

        for absolute_number, search in enumerate(
            searches,
            start=config.start,
        ):
            if config.resume and storage.is_completed(search):
                print(
                    f"[{absolute_number:03}] {search.query}\n"
                    "    - already completed; skipped"
                )

                skipped += 1
                continue

            print(
                f"[{absolute_number:03}] {search.query}"
            )

            query_succeeded = False

            for attempt in range(config.retries + 1):
                try:
                    page = browser.navigate(search.url)

                    browser.load_result_cards(
                        extractor.RESULT,
                        config.result_limit,
                    )

                    results = [
                        result
                        for result in extractor.extract(
                            page,
                            search,
                            config.result_limit,
                        )
                        if is_valid_result(result)
                    ]

                    saved = storage.save_results(results)

                    # Only mark the query completed after successful
                    # extraction and persistence.
                    storage.mark_completed(search)

                    videos += saved
                    completed += 1
                    query_succeeded = True

                    print(
                        f"    OK {len(results)} videos "
                        f"({saved} new)"
                    )

                    break

                except Exception as error:
                    if attempt < config.retries:
                        retry_number = attempt + 1

                        print(
                            f"    WARNING "
                            f"{type(error).__name__}; "
                            f"retry {retry_number}/{config.retries}"
                        )

                        logger.warning(
                            "Query %r attempt %d failed: %s",
                            search.query,
                            retry_number,
                            error,
                        )

                        continue

                    failed += 1

                    storage.save_error(
                        search,
                        error,
                        utc_now(),
                        attempt,
                    )

                    logger.exception(
                        "Query %r failed after %d retries",
                        search.query,
                        config.retries,
                    )

                    print(
                        f"    FAILED: {error}"
                    )

            # Delay only after a successful query and only if there
            # are more queries remaining in this run.
            if (
                query_succeeded
                and absolute_number < config.start + total - 1
            ):
                time.sleep(
                    random.uniform(
                        config.delay_min,
                        config.delay_max,
                    )
                )

    storage.write_summary(
        {
            "started_at": started_at,
            "finished_at": utc_now(),
            "start_query": config.start,
            "total_queries": total,
            "completed_queries": completed,
            "skipped_queries": skipped,
            "failed_queries": failed,
            "videos_collected": videos,
            "requested_results_per_query": config.result_limit,
        }
    )

    return 0


def main() -> None:
    try:
        raise SystemExit(run(parse_args()))
    except (ValueError, FileNotFoundError) as error:
        print(
            f"Error: {error}",
            file=sys.stderr,
        )
        raise SystemExit(2)


if __name__ == "__main__":
    main()