from __future__ import annotations

from typing import Any


class PlaywrightBrowser:
    """Thin adapter that owns browser lifecycle and navigation only."""

    def __init__(self, headless: bool, timeout_ms: int) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self.page: Any = None

    def __enter__(self) -> "PlaywrightBrowser":
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()

        self._browser = self._playwright.chromium.launch(
            headless=self.headless
        )

        self._context = self._browser.new_context(
            locale="es-ES",
            viewport={
                "width": 1440,
                "height": 1000,
            },
        )

        self.page = self._context.new_page()

        self.page.set_default_timeout(self.timeout_ms)

        return self

    def navigate(self, url: str) -> Any:
        """
        Navigate to a YouTube search page.

        YouTube may abort a navigation while the page is still usable,
        particularly when the browser redirects or replaces the document
        during loading. Therefore ERR_ABORTED is treated as recoverable if
        the expected result page becomes available.
        """

        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        try:
            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self.timeout_ms,
            )

        except PlaywrightTimeoutError:
            # The navigation may have loaded enough content despite the
            # timeout. Give the page a short opportunity to expose results.
            pass

        except Exception as error:
            message = str(error)

            if "ERR_ABORTED" not in message:
                raise

            # ERR_ABORTED can occur when YouTube replaces/redirects the
            # document during navigation. Continue and verify the page
            # instead of immediately treating it as a failed query.

        # Wait until YouTube has actually rendered video result cards.
        #
        # We intentionally use the DOM selector here only as a readiness
        # check. Extraction selectors remain owned by YouTubeExtractor.
        try:
            self.page.locator("ytd-video-renderer").first.wait_for(
                state="attached",
                timeout=self.timeout_ms,
            )
        except PlaywrightTimeoutError:
            raise RuntimeError(
                "YouTube search results did not load within "
                f"{self.timeout_ms / 1000:.1f} seconds: {url}"
            )

        return self.page

    def load_result_cards(
        self,
        selector: str,
        minimum_cards: int,
    ) -> int:
        """
        Trigger YouTube's normal lazy loading until enough cards are present.

        Search results are rendered incrementally. This adapter owns scrolling;
        the caller supplies the extractor-owned selector so selectors stay out
        of the browser layer.
        """

        cards = self.page.locator(selector)

        previous_count = cards.count()
        unchanged_scrolls = 0

        # A few extra cards allow the extractor to discard a duplicate or an
        # invalid/non-video card without ending below the requested result
        # limit.
        target_count = minimum_cards + 3

        for _ in range(8):
            if previous_count >= target_count:
                break

            self.page.evaluate(
                "window.scrollBy(0, Math.max(window.innerHeight * 0.9, 700))"
            )

            self.page.wait_for_timeout(750)

            current_count = cards.count()

            if current_count > previous_count:
                previous_count = current_count
                unchanged_scrolls = 0
            else:
                unchanged_scrolls += 1

                if unchanged_scrolls >= 2:
                    break

        return previous_count

    def __exit__(self, *_: object) -> None:
        if self._browser:
            self._browser.close()

        if self._playwright:
            self._playwright.stop()