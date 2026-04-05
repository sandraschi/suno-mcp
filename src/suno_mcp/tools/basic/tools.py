"""Basic Suno AI tools for music generation."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from ..shared.exceptions import BrowserError, SunoError
from ..shared.utils import SelectorHelper, get_shared_browser_manager


class BasicSunoTools:
    """Basic Suno AI tools for music generation."""

    def __init__(self) -> None:
        self.browser_manager = get_shared_browser_manager()
        self.logger = logging.getLogger(__name__)
        self.allow_programmatic_login = os.getenv(
            "SUNO_ENABLE_PROGRAMMATIC_LOGIN", ""
        ).lower() in ("1", "true", "yes")
        self.create_url = "https://suno.com/create"
        self.library_url = "https://suno.com/library"

    async def open_browser(self, headless: bool = True) -> str:
        """Open browser and navigate to Suno AI create page."""
        try:
            components = await self.browser_manager.ensure_browser(headless)
            page = components["page"]

            await page.goto(self.create_url, wait_until="networkidle")
            await page.wait_for_load_state("domcontentloaded")

            title = await page.title()
            url = page.url

            return f"✅ Browser opened successfully. Navigated to Suno AI.\nPage title: {title}\nURL: {url}\nHeadless mode: {headless}"

        except Exception as e:
            self.logger.error(f"Browser open failed: {e}")
            raise BrowserError(f"Browser initialization failed: {str(e)}", "BROWSER_INIT_ERROR")

    async def login(self, email: str, password: str) -> str:
        """Login to Suno AI account."""
        if not self.allow_programmatic_login:
            return (
                "🔒 Programmatic login is currently disabled.\n"
                "Use manual browser login and save/load session cookies instead.\n"
                "Set SUNO_ENABLE_PROGRAMMATIC_LOGIN=1 to re-enable scripted login."
            )
        try:
            components = await self.browser_manager.ensure_browser()
            page = components["page"]

            # Check if already logged in
            current_url = page.url
            if current_url and "/create" in current_url and "/login" not in current_url:
                return f"✅ Already logged in. Current URL: {current_url}\nReady for music generation!"

            # Try to find and click login button
            login_selectors = [
                'button:has-text("Sign in")',
                'a:has-text("Sign in")',
                'button:has-text("Login")',
                'a:has-text("Login")',
                '[data-testid="login-button"]',
                '.login-button',
            ]

            await SelectorHelper.try_selectors(page, login_selectors, "click")

            # Wait for login form
            await asyncio.sleep(2)

            # Fill email field
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="Email" i]',
                '#email',
                '[data-testid="email-input"]',
            ]

            await SelectorHelper.try_selectors(page, email_selectors, "fill", value=email)

            # Fill password field
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password" i]',
                'input[placeholder*="Password" i]',
                '#password',
                '[data-testid="password-input"]',
            ]

            await SelectorHelper.try_selectors(page, password_selectors, "fill", value=password)

            # Submit login
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Sign in")',
                'button:has-text("Login")',
                'button:has-text("Continue")',
                '[data-testid="submit-button"]',
                '.submit-button',
            ]

            await SelectorHelper.try_selectors(page, submit_selectors, "click")

            # Wait for navigation to create page or dashboard
            try:
                await page.wait_for_url("**/create/**", timeout=10000)
            except Exception:
                await asyncio.sleep(3)  # May have 2FA or other auth steps

            final_url = page.url
            is_logged_in = "/create" in final_url or "/library" in final_url

            return f"✅ Login {'successful' if is_logged_in else 'attempted'}. Current URL: {final_url}\n{'Ready for music generation!' if is_logged_in else 'May require additional authentication steps.'}"

        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            raise SunoError(f"Login failed: {str(e)}", "LOGIN_ERROR")

    async def generate_track(
        self,
        prompt: str,
        style: str = "synthwave",
        lyrics: Optional[str] = None,
        duration: str = "auto",
    ) -> str:
        """Generate a new music track using Suno AI."""
        try:
            components = await self.browser_manager.ensure_browser()
            page = components["page"]

            # Ensure we're on the create page
            if not page.url or "/create" not in page.url:
                await page.goto(self.create_url, wait_until="networkidle")
                await page.wait_for_load_state("domcontentloaded")

            # Wait for the form to be ready
            await asyncio.sleep(2)

            # Clear and fill the prompt field
            prompt_selectors = [
                'textarea[placeholder*="Describe" i]',
                'textarea[placeholder*="prompt" i]',
                'textarea[name="prompt"]',
                'textarea[data-testid="prompt-input"]',
                '.prompt-input',
                '#prompt',
            ]

            for selector in prompt_selectors:
                try:
                    await page.fill(selector, "")  # Clear first
                    await page.fill(selector, prompt)
                    break
                except Exception:
                    continue

            # Fill lyrics if provided
            if lyrics:
                lyrics_selectors = [
                    'textarea[placeholder*="lyrics" i]',
                    'textarea[placeholder*="Lyrics" i]',
                    'textarea[name="lyrics"]',
                    'textarea[data-testid="lyrics-input"]',
                    '.lyrics-input',
                ]
                await SelectorHelper.try_selectors(page, lyrics_selectors, "fill", value=lyrics)

            # Try to set style (may not be available in all versions)
            if style and style != "synthwave":
                style_selectors = [
                    'select[name="style"]',
                    'input[placeholder*="style" i]',
                    'select[data-testid="style-select"]',
                ]

                for selector in style_selectors:
                    try:
                        await page.select_option(selector, style)
                        break
                    except Exception:
                        try:
                            await page.fill(selector, style)
                            break
                        except Exception:
                            continue

            # Find and click the generate/create button
            generate_selectors = [
                'button:has-text("Create")',
                'button:has-text("Generate")',
                'button:has-text("Make Song")',
                'button[type="submit"]',
                '[data-testid="generate-button"]',
                '.generate-button',
            ]

            generate_clicked = await SelectorHelper.try_selectors(page, generate_selectors, "click")

            if not generate_clicked:
                raise SunoError("Could not find generate button", "GENERATE_ERROR")

            # Wait for generation to start (may show progress indicator)
            await asyncio.sleep(3)

            # Try to detect if generation started
            generation_started = False
            try:
                await page.wait_for_selector(
                    '[data-testid="generating"], .generating, [data-status="generating"]',
                    timeout=5000
                )
                generation_started = True
            except Exception:
                pass  # Generation may have started without visible indicator

            return f"🎵 Track generation {'started' if generation_started else 'initiated'}!\nPrompt: \"{prompt}\"\nStyle: {style}\n{f'Lyrics: {lyrics[:50]}...' if lyrics else ''}\n\nGeneration in progress... Use suno_get_status to check progress."

        except Exception as e:
            if isinstance(e, SunoError):
                raise
            self.logger.error(f"Track generation failed: {e}")
            raise SunoError(f"Track generation failed: {str(e)}", "GENERATE_ERROR")

    async def download_track(
        self,
        track_id: str,
        download_path: str = "downloads/",
        include_stems: bool = True,
    ) -> str:
        """Download a generated track from Suno AI library."""
        try:
            components = await self.browser_manager.ensure_browser()
            page = components["page"]

            # Navigate to library if not already there
            if not page.url or "/library" not in page.url:
                await page.goto(self.library_url, wait_until="networkidle")
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)

            # Look for the specific track
            track_found = False
            track_selectors = [
                f'[data-track-id="{track_id}"]',
                f'[data-song-id="{track_id}"]',
                f'a[href*="{track_id}"]',
                f'[data-testid="track-{track_id}"]',
            ]

            for selector in track_selectors:
                try:
                    track_element = page.locator(selector).first
                    if await track_element.count() > 0:
                        await track_element.click()
                        track_found = True
                        break
                except Exception:
                    continue

            if not track_found:
                # Try searching by scrolling and looking for tracks
                await asyncio.sleep(2)

                # Look for any track cards and try to find by content
                track_cards = page.locator('[data-testid*="track"], .track-card, .song-card')
                count = await track_cards.count()

                for i in range(count):
                    try:
                        card = track_cards.nth(i)
                        card_text = await card.text_content()
                        if card_text and track_id.lower()[:8] in card_text.lower():
                            await card.click()
                            track_found = True
                            break
                    except Exception:
                        continue

            if not track_found:
                raise SunoError(f"Track with ID \"{track_id}\" not found in library", "TRACK_NOT_FOUND")

            # Wait for track page to load
            await asyncio.sleep(2)

            # Set up download handling
            download_dir = Path(download_path)
            download_dir.mkdir(parents=True, exist_ok=True)

            # Handle main track download
            download_event = page.wait_for_event("download")
            download_selectors = [
                'button:has-text("Download")',
                'button:has-text("Export")',
                'a:has-text("Download")',
                '[data-testid="download-button"]',
                '.download-button',
            ]

            download_clicked = await SelectorHelper.try_selectors(page, download_selectors, "click")

            if not download_clicked:
                raise SunoError("Could not find download button", "DOWNLOAD_ERROR")

            # Wait for download to complete
            download = await download_event
            suggested_filename = download.suggested_filename
            full_path = download_dir / suggested_filename

            await download.save_as(str(full_path))

            # Handle stems download if requested
            stems_downloaded = False
            if include_stems:
                try:
                    stems_selectors = [
                        'button:has-text("Download Stems")',
                        'button:has-text("Export Stems")',
                        '[data-testid="stems-button"]',
                        '.stems-button',
                    ]

                    stems_download_event = page.wait_for_event("download")

                    for selector in stems_selectors:
                        try:
                            await page.click(selector, timeout=3000)
                            stems_download = await stems_download_event
                            stems_filename = stems_download.suggested_filename
                            stems_path = download_dir / stems_filename
                            await stems_download.save_as(str(stems_path))
                            stems_downloaded = True
                            break
                        except Exception:
                            continue
                except Exception:
                    pass  # Stems download failed, but main track succeeded

            return f"✅ Download completed!\nTrack: {suggested_filename}\nPath: {full_path}\nStems included: {stems_downloaded}\n\nTrack ID: {track_id}"

        except Exception as e:
            if isinstance(e, SunoError):
                raise
            self.logger.error(f"Download failed: {e}")
            raise SunoError(f"Download failed: {str(e)}", "DOWNLOAD_ERROR")

    async def get_status(self) -> str:
        """Get current Suno AI session status."""
        try:
            status = await self.browser_manager.get_status()

            return f"📊 Suno MCP Status:\nBrowser Open: {status.get('browser_open', False)}\nPage Ready: {status.get('page_ready', False)}\nCurrent URL: {status.get('current_url', 'None')}\nPage Title: {status.get('page_title', 'None')}\nIn Studio: {status.get('in_studio', False)}"

        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            raise SunoError(f"Status check failed: {str(e)}", "STATUS_ERROR")

    async def close_browser(self) -> str:
        """Close the browser session."""
        try:
            await self.browser_manager.close()
            return "✅ Browser closed successfully."

        except Exception as e:
            self.logger.error(f"Browser close failed: {e}")
            raise SunoError(f"Browser close failed: {str(e)}", "CLOSE_ERROR")

    async def get_browser_status(self) -> Dict[str, Any]:
        """Get detailed browser status for internal use."""
        return await self.browser_manager.get_status()
