"""Shared utilities for browser automation and tool helpers."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from .exceptions import BrowserError, SunoError


class SelectorHelper:
    """Helper class for robust element selection."""

    @staticmethod
    async def try_selectors(
        page: Page, selectors: list[str], action: str = "click", **kwargs
    ) -> bool:
        """Try multiple selectors for an action."""
        for selector in selectors:
            try:
                if action == "click":
                    await page.click(selector, timeout=2000, **kwargs)
                elif action == "fill":
                    await page.fill(selector, "", timeout=2000)  # Clear first
                    await page.fill(selector, kwargs.get("value", ""), timeout=2000)
                elif action == "select":
                    await page.select_option(selector, kwargs.get("value", ""), timeout=2000)
                return True
            except Exception:
                continue
        return False

    @staticmethod
    async def wait_for_any_selector(page: Page, selectors: list[str], **kwargs) -> Optional[str]:
        """Wait for any of the selectors to appear."""
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=2000, **kwargs)
                return selector
            except Exception:
                continue
        return None


class BrowserManager:
    """Manages browser lifecycle and sessions."""

    def __init__(self) -> None:
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.logger = logging.getLogger(__name__)

    async def ensure_browser(self, headless: bool = True) -> Dict[str, Any]:
        """Ensure browser is initialized and return browser components."""
        try:
            if not self.playwright:
                self.playwright = await async_playwright().start()

            if not self.browser:
                self.browser = await self.playwright.chromium.launch(
                    headless=headless,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-accelerated-2d-canvas",
                        "--no-first-run",
                        "--disable-gpu",
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor",
                    ],
                )

            if not self.context:
                self.context = await self.browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    accept_downloads=True,
                )

                # Set default download path
                downloads_path = Path("downloads")
                downloads_path.mkdir(exist_ok=True)

            if not self.page:
                self.page = await self.context.new_page()
                self.page.set_default_timeout(30000)
                self.page.set_default_navigation_timeout(30000)

                # Handle downloads
                self.page.on("download", lambda download: self._handle_download(download))

            return {
                "playwright": self.playwright,
                "browser": self.browser,
                "context": self.context,
                "page": self.page,
            }
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            raise BrowserError(f"Browser initialization failed: {str(e)}", "BROWSER_INIT_ERROR")

    async def _handle_download(self, download) -> None:
        """Handle file downloads."""
        try:
            downloads_path = Path("downloads")
            downloads_path.mkdir(exist_ok=True)

            filename = download.suggested_filename
            filepath = downloads_path / filename

            await download.save_as(str(filepath))
            self.logger.info(f"Downloaded file: {filepath}")

        except Exception as e:
            self.logger.error(f"Download failed: {e}")

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            self.logger.info("Browser session closed successfully")

        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")
            raise BrowserError(f"Browser cleanup failed: {str(e)}", "BROWSER_CLOSE_ERROR")

    async def get_status(self) -> Dict[str, Any]:
        """Get current browser status."""
        try:
            status = {
                "browser_open": self.browser is not None,
                "context_ready": self.context is not None,
                "page_ready": self.page is not None,
                "current_url": None,
                "page_title": None,
                "in_studio": False,
            }

            if self.page:
                try:
                    status["current_url"] = self.page.url
                    status["page_title"] = await self.page.title()
                    status["in_studio"] = "/studio" in (self.page.url or "")
                except Exception:
                    pass  # Page might be closed or unavailable

            return status

        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            return {
                "browser_open": False,
                "context_ready": False,
                "page_ready": False,
                "current_url": None,
                "page_title": None,
                "in_studio": False,
                "error": str(e),
            }


_shared_browser_manager: Optional[BrowserManager] = None


def get_shared_browser_manager() -> BrowserManager:
    """Single Playwright Chromium session shared by suno_* and recon_* tools."""

    global _shared_browser_manager
    if _shared_browser_manager is None:
        _shared_browser_manager = BrowserManager()
    return _shared_browser_manager


class ConfigManager:
    """Configuration management for the MCP server."""

    def __init__(self) -> None:
        self.config = {
            "browser": {
                "headless": True,
                "default_viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            "timeouts": {
                "navigation": 30000,
                "element": 10000,
                "page_load": 60000,
            },
            "paths": {
                "downloads": "downloads/",
                "temp": "temp/",
                "exports": "exports/",
            },
            "suno": {
                "base_url": "https://app.suno.ai",
                "studio_url": "https://studio.suno.ai",
                "api_timeout": 120000,
            },
            "security": {
                "max_concurrent_sessions": 3,
                "session_timeout": 3600000,  # 1 hour
                "rate_limit": {
                    "requests_per_minute": 60,
                    "burst_limit": 10,
                },
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot notation key."""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value


# Global config instance
config = ConfigManager()
