from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    input_path: Path
    output_dir: Path
    result_limit: int = 10
    query_limit: int | None = None
    resume: bool = False
    headless: bool = False
    delay_min: float = 2.0
    delay_max: float = 5.0
    retries: int = 2
    navigation_timeout_ms: int = 30_000

    def __post_init__(self) -> None:
        if self.result_limit < 1:
            raise ValueError("--limit must be at least 1")
        if self.query_limit is not None and self.query_limit < 1:
            raise ValueError("--queries must be at least 1")
        if self.delay_min < 0 or self.delay_max < self.delay_min:
            raise ValueError("delays must be non-negative and --delay-max >= --delay-min")
        if self.retries < 0:
            raise ValueError("--retries cannot be negative")
