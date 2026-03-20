"""Reconnaissance tools for Suno Studio DOM analysis.

These tools enable browser-based reconnaissance of the Suno Studio interface
to discover selectors, map UI elements, and capture the DOM structure for
automation development.

Since Suno has no public API, these tools help identify:
- Interactive elements (buttons, sliders, inputs)
- Timeline/track structure
- Stem generation controls
- Export options
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import Page

from ..shared.exceptions import BrowserError, SunoError
from ..shared.utils import BrowserManager, SelectorHelper


class ReconTools:
    """Reconnaissance tools for Suno Studio DOM mapping."""

    def __init__(self) -> None:
        self.browser_manager = BrowserManager()
        self.logger = logging.getLogger(__name__)
        self.recon_dir = Path("recon_output")
        self.recon_dir.mkdir(exist_ok=True)

    async def start_recon_session(self, headless: bool = False) -> str:
        """
        Start a reconnaissance session with non-headless browser.
        
        Opens browser in visible mode so user can manually authenticate
        with Suno AI before running DOM capture operations.
        
        Args:
            headless: Run in headless mode (default False for recon)
            
        Returns:
            Session status and instructions for manual login
        """
        try:
            components = await self.browser_manager.ensure_browser(headless=headless)
            page = components["page"]
            
            # Navigate to Suno Studio
            await page.goto("https://suno.com/studio", wait_until="networkidle")
            await asyncio.sleep(2)
            
            current_url = page.url
            title = await page.title()
            
            # Check if we hit auth wall
            is_auth_required = "login" in current_url.lower() or "sign" in current_url.lower()
            
            return f"""🔍 **Recon Session Started**

**Browser:** Chromium ({"headless" if headless else "visible"} mode)
**Target:** Suno Studio
**Current URL:** {current_url}
**Page Title:** {title}

**Auth Status:** {"⚠️ Login required - please authenticate manually" if is_auth_required else "✅ Page loaded"}

**Next Steps:**
1. {"Complete login in the browser window" if is_auth_required else "Navigate to Studio if not already there"}
2. Wait for Studio interface to fully load
3. Run `capture_studio_dom()` to analyze the interface
4. Use `find_interactive_elements()` to map controls

**Note:** Keep this session open - closing will require re-authentication.
"""
        except Exception as e:
            self.logger.error(f"Recon session start failed: {e}")
            raise BrowserError(f"Recon session failed: {str(e)}", "RECON_INIT_ERROR")

    async def ensure_authenticated_session(
        self,
        cookie_filename: str = "suno_cookies.json",
        navigate_to: str = "https://suno.com/create",
        headless: bool = False,
    ) -> str:
        """
        Ensure authenticated session using manual login + persisted cookies.

        Workflow:
        1) Open browser and attempt cookie restore.
        2) Navigate to target URL.
        3) If auth wall detected, ask user to login manually and save cookies.
        """
        try:
            components = await self.browser_manager.ensure_browser(headless=headless)
            page = components["page"]

            cookie_path = self.recon_dir / cookie_filename
            cookies_loaded = False
            if cookie_path.exists():
                try:
                    cookies = json.loads(cookie_path.read_text(encoding="utf-8"))
                    await components["context"].add_cookies(cookies)
                    cookies_loaded = True
                except Exception:
                    cookies_loaded = False

            await page.goto(navigate_to, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            current_url = page.url
            lower_url = current_url.lower()
            auth_required = any(k in lower_url for k in ("sign-in", "login", "auth", "/l/"))

            if auth_required:
                return f"""🔐 **Authentication Required**

Target URL: {navigate_to}
Current URL: {current_url}
Cookies loaded: {cookies_loaded}

Please login manually in the browser window, then run:
1. `recon_save_cookies("{cookie_filename}")`
2. `recon_ensure_authenticated_session("{cookie_filename}")` again
"""

            return f"""✅ **Authenticated Session Ready**

Target URL: {navigate_to}
Current URL: {current_url}
Cookies loaded: {cookies_loaded}
Headless: {headless}
"""
        except Exception as e:
            self.logger.error(f"Ensure authenticated session failed: {e}")
            raise SunoError(
                f"Ensure authenticated session failed: {str(e)}",
                "AUTH_SESSION_ERROR",
            )

    async def capture_studio_dom(
        self,
        save_html: bool = True,
        save_json: bool = True,
    ) -> str:
        """
        Capture the current Suno Studio DOM structure.
        
        Saves the full HTML and extracts structured data about
        interactive elements, containers, and potential automation targets.
        
        Args:
            save_html: Save raw HTML to file
            save_json: Save structured analysis to JSON
            
        Returns:
            Summary of captured elements and file paths
        """
        try:
            components = await self.browser_manager.ensure_browser()
            page = components["page"]
            
            current_url = page.url
            
            # Verify we're in Studio
            if "/studio" not in current_url:
                return f"""⚠️ **Not in Studio**

Current URL: {current_url}

Please navigate to Suno Studio first, then run this command again.
You can use: `await page.goto("https://suno.com/studio")`
"""
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Capture full HTML
            html_content = await page.content()
            
            if save_html:
                html_path = self.recon_dir / f"studio_dom_{timestamp}.html"
                html_path.write_text(html_content, encoding="utf-8")
            
            # Analyze DOM structure
            analysis = await self._analyze_dom(page)
            
            if save_json:
                json_path = self.recon_dir / f"studio_analysis_{timestamp}.json"
                json_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
            
            # Generate summary
            summary = self._generate_summary(analysis)
            
            return f"""🔍 **Studio DOM Captured**

**URL:** {current_url}
**Timestamp:** {timestamp}

**Files Saved:**
{"• HTML: " + str(html_path) if save_html else ""}
{"• JSON: " + str(json_path) if save_json else ""}

**Element Summary:**
{summary}

**Potential Automation Targets:**
• Buttons: {len(analysis.get('buttons', []))}
• Inputs: {len(analysis.get('inputs', []))}
• Sliders: {len(analysis.get('sliders', []))}
• Timeline elements: {len(analysis.get('timeline', []))}
• Track elements: {len(analysis.get('tracks', []))}

Use `find_interactive_elements()` for detailed element mapping.
"""
        except Exception as e:
            self.logger.error(f"DOM capture failed: {e}")
            raise SunoError(f"DOM capture failed: {str(e)}", "DOM_CAPTURE_ERROR")

    async def periodic_dom_snapshots(
        self,
        interval_seconds: int = 30,
        iterations: int = 6,
        prefix: str = "periodic",
        include_element_map: bool = False,
    ) -> str:
        """
        Capture periodic DOM/screenshot snapshots for UI drift detection.

        Args:
            interval_seconds: seconds between snapshots
            iterations: number of snapshots to capture
            prefix: output filename prefix
            include_element_map: also save interactive element maps on each iteration
        """
        try:
            components = await self.browser_manager.ensure_browser()
            page = components["page"]
            current_url = page.url or "(unknown)"
            if iterations < 1:
                iterations = 1
            if interval_seconds < 1:
                interval_seconds = 1

            saved_files: list[str] = []
            for i in range(iterations):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                shot_name = f"{prefix}_screenshot_{i+1:02d}_{timestamp}.png"
                html_name = f"{prefix}_dom_{i+1:02d}_{timestamp}.html"
                json_name = f"{prefix}_analysis_{i+1:02d}_{timestamp}.json"

                screenshot_path = self.recon_dir / shot_name
                html_path = self.recon_dir / html_name
                json_path = self.recon_dir / json_name

                await page.screenshot(path=str(screenshot_path), full_page=True)
                html_content = await page.content()
                html_path.write_text(html_content, encoding="utf-8")
                analysis = await self._analyze_dom(page)
                json_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

                saved_files.extend([str(screenshot_path), str(html_path), str(json_path)])

                if include_element_map:
                    map_name = f"{prefix}_elements_{i+1:02d}_{timestamp}.json"
                    map_path = self.recon_dir / map_name
                    element_map = await self._collect_interactive_elements(page)
                    map_path.write_text(json.dumps(element_map, indent=2), encoding="utf-8")
                    saved_files.append(str(map_path))

                if i < iterations - 1:
                    await asyncio.sleep(interval_seconds)

            return (
                f"🕒 **Periodic snapshots completed**\n\n"
                f"URL: {current_url}\n"
                f"Iterations: {iterations}\n"
                f"Interval: {interval_seconds}s\n"
                f"Saved files: {len(saved_files)}\n"
                f"Output directory: {self.recon_dir}\n"
            )
        except Exception as e:
            self.logger.error(f"Periodic snapshots failed: {e}")
            raise SunoError(
                f"Periodic snapshots failed: {str(e)}",
                "PERIODIC_SNAPSHOT_ERROR",
            )

    async def _analyze_dom(self, page: Page) -> Dict[str, Any]:
        """Analyze DOM structure and extract key elements."""
        analysis = {
            "url": page.url,
            "title": await page.title(),
            "timestamp": datetime.now().isoformat(),
            "buttons": [],
            "inputs": [],
            "sliders": [],
            "timeline": [],
            "tracks": [],
            "stems": [],
            "controls": [],
            "data_attributes": [],
        }
        
        # Find buttons
        buttons = await page.query_selector_all("button")
        for btn in buttons[:50]:  # Limit to prevent timeout
            try:
                text = await btn.text_content()
                attrs = await self._get_element_attrs(btn)
                if text or attrs.get("class") or attrs.get("data-testid"):
                    analysis["buttons"].append({
                        "text": (text or "").strip()[:100],
                        "attributes": attrs,
                        "visible": await btn.is_visible(),
                    })
            except Exception:
                continue
        
        # Find inputs
        inputs = await page.query_selector_all("input, textarea")
        for inp in inputs[:30]:
            try:
                attrs = await self._get_element_attrs(inp)
                analysis["inputs"].append({
                    "type": attrs.get("type", "text"),
                    "placeholder": attrs.get("placeholder"),
                    "name": attrs.get("name"),
                    "attributes": attrs,
                })
            except Exception:
                continue
        
        # Find sliders/range inputs
        sliders = await page.query_selector_all('input[type="range"], [role="slider"]')
        for slider in sliders[:20]:
            try:
                attrs = await self._get_element_attrs(slider)
                analysis["sliders"].append({
                    "attributes": attrs,
                    "aria_label": attrs.get("aria-label"),
                })
            except Exception:
                continue
        
        # Find timeline-related elements
        timeline_selectors = [
            '[class*="timeline" i]',
            '[class*="track" i]',
            '[class*="stem" i]',
            '[class*="waveform" i]',
            '[data-testid*="timeline" i]',
            '[data-testid*="track" i]',
        ]
        
        for selector in timeline_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for el in elements[:10]:
                    attrs = await self._get_element_attrs(el)
                    tag = await el.evaluate("el => el.tagName.toLowerCase()")
                    analysis["timeline"].append({
                        "selector": selector,
                        "tag": tag,
                        "attributes": attrs,
                    })
            except Exception:
                continue
        
        # Find elements with data-* attributes (often automation-friendly)
        data_elements = await page.query_selector_all("[data-testid], [data-track], [data-stem], [data-id]")
        for el in data_elements[:50]:
            try:
                attrs = await self._get_element_attrs(el)
                tag = await el.evaluate("el => el.tagName.toLowerCase()")
                analysis["data_attributes"].append({
                    "tag": tag,
                    "attributes": {k: v for k, v in attrs.items() if k.startswith("data-")},
                })
            except Exception:
                continue
        
        return analysis

    async def _get_element_attrs(self, element) -> Dict[str, str]:
        """Extract all attributes from an element."""
        try:
            return await element.evaluate("""el => {
                const attrs = {};
                for (const attr of el.attributes) {
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            }""")
        except Exception:
            return {}

    def _generate_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate human-readable summary of analysis."""
        lines = []
        
        # Interesting buttons
        interesting_buttons = [
            b for b in analysis.get("buttons", [])
            if b.get("text") and any(
                kw in b["text"].lower() 
                for kw in ["generate", "create", "add", "export", "download", "save", "play", "stem"]
            )
        ]
        if interesting_buttons:
            lines.append("**Key Buttons Found:**")
            for btn in interesting_buttons[:5]:
                lines.append(f"  • \"{btn['text'][:40]}\"")
        
        # Data attributes (good for stable selectors)
        data_attrs = analysis.get("data_attributes", [])
        testids = [d for d in data_attrs if d.get("attributes", {}).get("data-testid")]
        if testids:
            lines.append(f"\n**data-testid Elements:** {len(testids)} found (great for automation!)")
            for t in testids[:5]:
                lines.append(f"  • {t['tag']}[data-testid=\"{t['attributes'].get('data-testid')}\"]")
        
        return "\n".join(lines) if lines else "No notable elements found - Studio may not be fully loaded."

    async def find_interactive_elements(self) -> str:
        """
        Find and catalog all interactive elements in the current page.
        
        Maps buttons, inputs, sliders, and clickable elements with
        their selectors for automation scripting.
        
        Returns:
            Detailed mapping of interactive elements with suggested selectors
        """
        try:
            components = await self.browser_manager.ensure_browser()
            page = components["page"]
            elements = await self._collect_interactive_elements(page)
            
            # Format output
            output = ["🎯 **Interactive Elements Map**\n"]
            
            if elements["clickable"]:
                output.append("**Clickable Elements:**")
                for el in elements["clickable"][:20]:
                    if el["text"] or el["testid"]:
                        output.append(f"  • {el['text'] or el['testid']} → `{el['selector']}`")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = self.recon_dir / f"interactive_elements_{timestamp}.json"
            json_path.write_text(json.dumps(elements, indent=2), encoding="utf-8")
            
            output.append(f"\n**Full mapping saved to:** {json_path}")
            
            return "\n".join(output)
            
        except Exception as e:
            self.logger.error(f"Element mapping failed: {e}")
            raise SunoError(f"Element mapping failed: {str(e)}", "ELEMENT_MAP_ERROR")

    async def _collect_interactive_elements(self, page: Page) -> Dict[str, Any]:
        """Collect interactive elements and best-effort selectors."""
        elements: Dict[str, Any] = {
            "clickable": [],
            "inputs": [],
            "sliders": [],
            "dropdowns": [],
        }

        clickable = await page.query_selector_all(
            "button, a, [role='button'], [onclick], [tabindex='0']"
        )
        for el in clickable[:100]:
            try:
                if await el.is_visible():
                    text = (await el.text_content() or "").strip()[:50]
                    attrs = await self._get_element_attrs(el)
                    tag = await el.evaluate("el => el.tagName.toLowerCase()")
                    selector = self._build_selector(tag, attrs, text)
                    elements["clickable"].append(
                        {
                            "text": text,
                            "tag": tag,
                            "selector": selector,
                            "testid": attrs.get("data-testid"),
                        }
                    )
            except Exception:
                continue
        return elements

    def _build_selector(self, tag: str, attrs: Dict[str, str], text: str) -> str:
        """Build the most stable selector for an element."""
        # Prefer data-testid
        if attrs.get("data-testid"):
            return f'[data-testid="{attrs["data-testid"]}"]'
        
        # Then ID
        if attrs.get("id"):
            return f'#{attrs["id"]}'
        
        # Then aria-label
        if attrs.get("aria-label"):
            return f'{tag}[aria-label="{attrs["aria-label"]}"]'
        
        # Then text content for buttons
        if tag == "button" and text:
            safe_text = text.replace('"', '\\"')[:30]
            return f'{tag}:has-text("{safe_text}")'
        
        # Fallback to class (less stable)
        if attrs.get("class"):
            first_class = attrs["class"].split()[0]
            return f'{tag}.{first_class}'
        
        return tag

    async def save_cookies(self, filename: str = "suno_cookies.json") -> str:
        """
        Save current session cookies for reuse.
        
        Saves authentication cookies so future sessions can skip
        manual login (until cookies expire).
        
        Args:
            filename: Output filename for cookies JSON
            
        Returns:
            Confirmation with cookie count and expiry info
        """
        try:
            components = await self.browser_manager.ensure_browser()
            context = components["context"]
            
            cookies = await context.cookies()
            
            cookie_path = self.recon_dir / filename
            cookie_path.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
            
            # Analyze cookies
            auth_cookies = [c for c in cookies if "session" in c["name"].lower() or "auth" in c["name"].lower()]
            
            return f"""🍪 **Cookies Saved**

**File:** {cookie_path}
**Total Cookies:** {len(cookies)}
**Auth-related Cookies:** {len(auth_cookies)}

**Notable Cookies:**
{chr(10).join(f"  • {c['name']} (expires: {c.get('expires', 'session')})" for c in auth_cookies[:5])}

**Usage:** Load these cookies in future sessions to skip login:
```python
await context.add_cookies(json.load(open("{filename}")))
```
"""
        except Exception as e:
            self.logger.error(f"Cookie save failed: {e}")
            raise SunoError(f"Cookie save failed: {str(e)}", "COOKIE_SAVE_ERROR")

    async def load_cookies(self, filename: str = "suno_cookies.json") -> str:
        """
        Load previously saved cookies into current session.
        
        Args:
            filename: Cookie file to load
            
        Returns:
            Status of cookie restoration
        """
        try:
            cookie_path = self.recon_dir / filename
            
            if not cookie_path.exists():
                return f"❌ Cookie file not found: {cookie_path}\n\nRun `save_cookies()` first after manual login."
            
            cookies = json.loads(cookie_path.read_text(encoding="utf-8"))
            
            components = await self.browser_manager.ensure_browser()
            context = components["context"]
            
            await context.add_cookies(cookies)
            
            # Refresh page to apply cookies
            page = components["page"]
            await page.reload()
            await asyncio.sleep(2)
            
            current_url = page.url
            
            return f"""🍪 **Cookies Loaded**

**Cookies Restored:** {len(cookies)}
**Current URL:** {current_url}

{"✅ Appears to be authenticated!" if "/studio" in current_url and "login" not in current_url else "⚠️ May need to re-authenticate - cookies might be expired."}
"""
        except Exception as e:
            self.logger.error(f"Cookie load failed: {e}")
            raise SunoError(f"Cookie load failed: {str(e)}", "COOKIE_LOAD_ERROR")

    async def take_screenshot(self, filename: str = None) -> str:
        """
        Take a screenshot of the current page.
        
        Args:
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to saved screenshot
        """
        try:
            components = await self.browser_manager.ensure_browser()
            page = components["page"]
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"studio_screenshot_{timestamp}.png"
            
            screenshot_path = self.recon_dir / filename
            await page.screenshot(path=str(screenshot_path), full_page=True)
            
            return f"📸 **Screenshot Saved**\n\nPath: {screenshot_path}"
            
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            raise SunoError(f"Screenshot failed: {str(e)}", "SCREENSHOT_ERROR")

    async def close_session(self) -> str:
        """Close the reconnaissance session and browser."""
        try:
            await self.browser_manager.close()
            return "✅ Recon session closed. Browser terminated."
        except Exception as e:
            self.logger.error(f"Session close failed: {e}")
            raise BrowserError(f"Session close failed: {str(e)}", "SESSION_CLOSE_ERROR")
