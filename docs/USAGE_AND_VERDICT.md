# Usage reality & verdict

## Is this minimally useful for making music with Suno?

**As a reliable “press button, get MP3 forever” pipeline: no.** Suno has no stable public API here; generation and download depend on **DOM selectors** in `src/suno_mcp/tools/basic/tools.py` that **break when Suno changes the site**.

**As a practical glue layer for someone who already uses Suno in a browser: marginally yes**, if you accept:

1. **You use Playwright’s Chromium** (started by this MCP), not your everyday Chrome profile, unless you add CDP attach yourself.
2. **You log in manually** (or cookie save/load) and often **finish the musical workflow in the visible Suno UI** when automation fails.
3. **You use recon** when things break: `recon_capture_page` / `recon_capture_dom`, `recon_find_elements`, files under `recon_output/`, then **patch selectors** (or accept manual operation).

So: **“making music”** in the sense Suno intends is still mostly **you + Suno’s UI**; this repo is **orchestration, status, HTTP, MCP tooling, and DOM forensics**—not a vendor-grade integration.

## When it’s worth keeping

- You want **MCP tools + FastAPI** around a single Playwright session.
- You will **maintain selectors** occasionally or lean on **human-in-the-loop**.
- You value **recon artifacts** (HTML/JSON maps) for debugging automation.
- You use the **web_sota** **Recon** page (`/recon`) to trigger capture without only using an MCP client.

## When to delete or archive

- You need **unattended, stable** production automation (use an official API or a different product).
- You are **not willing** to touch Python when Suno updates the UI.
- The repo only causes shame—**a private archive or deletion is a valid outcome**.

## Minimal “try to make a track” flow (honest)

1. `uv sync` / `playwright install chromium` / run MCP or `web_sota/start.ps1`.
2. `suno_open_browser(headless=false)` or `recon_start_session` — **log in manually** in the Playwright window.
3. `recon_save_cookies` (optional) for next time.
4. Attempt `suno_generate_track` / `suno_download_track` — **if** selectors match, you get automation; **if not**, use Suno in that same window by hand and treat the repo as **session + recon only**.
5. On failure: **`recon_capture_page`** (any URL) or **`recon_capture_dom`** (expects Studio), **`recon_find_elements`**, edit `tools/basic/tools.py`, retry.

**Bottom line:** It can be **minimally useful** for music **only** if you treat Suno as the real product and this repo as **optional automation + debugging**. It is **not** a substitute for Suno’s own app when the DOM drifts.
