from __future__ import annotations

from typing import Any


class PlaywrightBrowser:
    """Thin adapter that owns browser lifecycle and navigation only."""

    def __init__(self, headless: bool, timeout_ms: int) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._playwright: Any = None
        self._browser: Any = None
        self.page: Any = None

    def __enter__(self) -> "PlaywrightBrowser":
        from playwright.sync_api import sync_playwright
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        context = self._browser.new_context(locale="es-ES", viewport={"width": 1440, "height": 1000})
        self.page = context.new_page()
        self.page.set_default_timeout(self.timeout_ms)
        return self

    def navigate(self, url: str) -> Any:
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        return self.page

    def __exit__(self, *_: object) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
