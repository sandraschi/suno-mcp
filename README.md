# Suno-MCP

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>


> 📖 **[Installation Guide](INSTALL.md)** — quick start, manual setup, and troubleshooting

MCP server that drives **suno.com in a browser** via Playwright. There is **no official Suno API** in this projectonly brittle UI automation against a site that changes whenever Suno ships an update.

## Is this useless?

**For hands-off, reliable Suno automation: basically yes  do not depend on it.** There is no stable API contract; Sunos UI changes; nothing here is a supported integration.

**Not literally useless:** it is still a **wired-up MCP + Playwright + cookie/recon shell**. It can be worth using if you accept **human-in-the-loop** (you drive Suno in the browser; tools help with status, capture, cookies) or **you** own **selector fixes** when things break. Treat it as a **scratchpad or experiment**, not a turnkey product.

## What it can do today (be precise)

**Human in the loop here is not** I opened suno.com in Edge/Chrome on my desktop and the MCP reads it. **It is not.** Tools only see **Playwrights Chromium** that this process starts. Your normal browser profile is **invisible** to the server unless someone adds **CDP attach to an existing browser** (not in this repo).

**What actually works in that Playwright window:**

| Capability | Notes |
|------------|--------|
| **One shared browser** | `suno_*` and `recon_*` share a **single** `BrowserManager` sessionlog in once, then DOM capture / cookies / `suno_get_status` refer to the **same** page. |
| **Navigate** | e.g. create page (`suno_open_browser`), or Studio (`recon_start_session` goes to `/studio`). |
| **Status (URL/title)** | `suno_get_status`, and FastAPI `GET /api/v1/status`, read Playwrights current pagenot Sunos servers idea of generation done. |
| **Recon** | Save HTML/JSON of the DOM, map buttons/inputs, screenshots, **save/load cookies**the useful part when automation selectors rot. |
| **Generate / download** | **Only if** todays suno.com still matches the selectors in `src/suno_mcp/tools/basic/tools.py`. Treat as **-effort**; often the first thing to break. |
| **MCP stdio** | Claude / Cursor invoke the same tools as below. |
| **FastAPI** | `GET /health`, `GET /api/v1/status`, `GET /api/v1/tools`, `POST /api/v1/tools/{tool_name}`  HTTP mirror of tool execution. |

**`web_sota` (Vite dashboard):** **Dashboard** and **Status** call `GET /health` and `GET /api/v1/status`. **Recon** (`/recon`) triggers **`POST /api/v1/recon/capture-current`** and **`POST /api/v1/recon/find-elements`** on the shared Playwright page (same session as MCP). Set **`VITE_API_BASE_URL`** if the API is not on `http://127.0.0.1:10883` (see `web_sota/.env.example`). Other routes may still be stubs.

### Making it work better (realistic)

1. **Keep selectors current**  When Suno ships UI changes, update `tools/basic/tools.py` (use **`recon_capture_page`** / **`recon_find_elements`** or the **`/recon`** web UI to inspect the DOM).
2. **Optional hard mode**  Attach Playwright to **your** Chrome via CDP so human in the loop could mean your real profile; thats new design work, not a config toggle.

**Docs:** [docs/USAGE_AND_VERDICT.md](docs/USAGE_AND_VERDICT.md) (keep vs delete, making music honesty), [docs/WEB_RECON.md](docs/WEB_RECON.md) (web recon + API).

## Keep this repo or delete it?

| Situation | Suggestion |
|-----------|------------|
| You want **zero maintenance** and **hands-off music generation** | **Delete or archive.** This will disappoint you. |
| Youre OK with **Suno in the browser** (often by hand) and use MCP/recon as **glue + forensics** | **Keep.** Its now **minimally useful** for that: shared Playwright session, real dashboard/status, **`/recon`** to dump DOM and maps into `recon_output/`, FastAPI for HTTP. |
| The repo only triggers shame | **Private or delete** is validno moral obligation to maintain a public demo. |

There is no magic upgrade path inside this repo that turns Sunos live SPA into a stable API. **Minimal usefulness for music** = **you** still drive Suno; this stack helps **session, capture, and occasional scripted clicks** when selectors still match.

## What this actually is

| Reality | Detail |
|--------|--------|
| **Integration model** | Remote-control the live web app (`https://suno.com/...`). Selectors in code are **-effort guesses** (`data-testid`, text, tags). When Suno changes the DOM, **flows break** until someone updates the Python. |
| **Login** | Programmatic login is **off by default** (`SUNO_ENABLE_PROGRAMMATIC_LOGIN` must be `1` to try it). The practical path is **manual login** in a visible browser, then **cookie save/load** via the `recon_*` tools. |
| **Generation / download** | Same fragility: `suno_generate_track` and `suno_download_track` assume the current create/library UI still matches the selectors in `src/suno_mcp/tools/basic/tools.py`. **No guarantee** they work on todays Suno. |
| **Recon tools** | `recon_capture_dom`, `recon_find_elements`, etc. exist **because** automation breaks they dump DOM / map elements so you can **see what changed**, not because Studio is solved. |
| **Suno Studio** | **Not implemented.** There are no `suno_studio_*` tools in the codebase. Any README or doc that describes full Studio timelines, stems, export pipelines, etc. is **fiction** unless added later as real code. |
| **MCP / HTTP server** | The Python package (FastMCP, FastAPI, optional `web_sota` + uvicorn) can run regardless of Sunothat part is works. **Whether Suno actions succeed** is a separate question. |

**Bottom line:** Treat this as an **experimental bridge**, not a supported Suno product. Expect **manual intervention**, **selector maintenance**, and **sudden breakage** after site changes.

## What ships in code (real tools)

Rough count: **6** `suno_*`, **10** `recon_*` (includes **`recon_capture_page`** for any URL), plus `help`, `get_server_status`, and **`agentic_suno_workflow`** (needs FastMCP sampling + a reachable LLMsee env vars below).

| Area | Tools |
|------|--------|
| Browser / Suno UI | `suno_open_browser`, `suno_login`, `suno_generate_track`, `suno_download_track`, `suno_get_status`, `suno_close_browser` |
| Recon / session | `recon_start_session`, `recon_capture_dom` (Studio-oriented), **`recon_capture_page`** (current URL), `recon_find_elements`, `recon_save_cookies`, `recon_load_cookies`, `recon_screenshot`, `recon_ensure_authenticated_session`, `recon_periodic_dom_snapshots`, `recon_close_session` |
| Other | `help`, `get_server_status`, `agentic_suno_workflow` |

If a feature is not in this list, **it does not exist** in this repo.

## FastMCP 3.1.0x extras

- **Sampling / agentic:** Configure `SUNO_SAMPLING_BASE_URL` (default `http://127.0.0.1:11434/v1`), `SUNO_SAMPLING_MODEL`, optional `SUNO_SAMPLING_API_KEY`; `SUNO_SAMPLING_USE_CLIENT_LLM=1` to prefer the host LLM; `SUNO_SAMPLING_USE_OPENAI_KEY=1` uses `OPENAI_API_KEY` for cloud endpoints.
- **Skills:** Bundled `skill://music-generation/SKILL.md` (if present in package).

## Requirements

- **Python 3.12+** (see `pyproject.toml`)
- **Windows** is the primary target for the Playwright + service story; other OSes may run the MCP but browser paths are untested here.
- **Playwright Chromium:** `playwright install chromium`

## Quick Start

```powershell
git clone https://github.com/sandraschi/suno-mcp
cd suno-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:


## Install (development)

```powershell
git clone https://github.com/sandraschi/suno-mcp.git
Set-Location suno-mcp
uv sync
playwright install chromium
uv run suno-mcp
```

## Claude Desktop (example)

```json
"mcpServers": {
  "suno-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/suno-mcp", "run", "suno-mcp"]
  }
}
```

Adjust `--directory` to your clone. Config file locations: Windows `%APPDATA%\Claude\claude_desktop_config.json`, macOS `~/Library/Application Support/Claude/`, Linux `~/.config/Claude/`.

## Web dashboard (`web_sota`)

Optional Vite UI + FastAPI backend; `web_sota/start.ps1` starts frontend/backend on ports defined there. Backend loads **`suno_mcp.server:app`** (FastAPI). This does **not** fix Suno selector driftits only a shell around the same fragile automation.

## Documentation

- **[docs/README.md](docs/README.md)**  index
- **[docs/USAGE_AND_VERDICT.md](docs/USAGE_AND_VERDICT.md)**  making music (honest), keep vs delete
- **[docs/WEB_RECON.md](docs/WEB_RECON.md)**  `/recon` web UI and recon API routes

Older ad-hoc markdown may be aspirational. **Trust `README.md` + `src/suno_mcp/`** for what actually exists.

## Troubleshooting (honest)

1. **Nothing clicks / fills**  Suno changed the UI. Use **`recon_capture_page`** (any page) or `recon_capture_dom` (Studio), **`recon_find_elements`**, or the **`/recon`** web page; compare output to `tools/basic/tools.py`, update selectors, or use manual control only.
2. **Login tool disabled**  By design; use cookies or set `SUNO_ENABLE_PROGRAMMATIC_LOGIN=1` (still may fail with 2FA or UI changes).
3. **Playwright errors**  Run with `headless=false`, watch the window, confirm you can complete the flow by hand first.


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.

## License

MIT License

---

**Author:** Sandra Schipal (@sandraschi)  
**Status:** Experimental browser automation; not production ready in any sense that implies Suno will keep working without ongoing maintenance.
