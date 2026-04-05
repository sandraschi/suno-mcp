# Web dashboard: live status & recon

## What is real vs stub

| Route | Data |
|-------|------|
| `/` (Dashboard) | **Live** — `GET /health`, `GET /api/v1/status` |
| `/status` | **Live** — same endpoints |
| `/recon` | **Live** — `POST /api/v1/recon/capture-current`, `POST /api/v1/recon/find-elements`, `GET /api/v1/recon/output-dir` |
| `/apps`, `/chat`, `/help`, `/settings`, `/tools` | Mostly **static** placeholders unless noted otherwise |

## Backend base URL

Vite defaults to talking to the FastAPI app at **`http://127.0.0.1:10883`** (see `web_sota/start.ps1`). Override with **`VITE_API_BASE_URL`** (see `web_sota/.env.example`).

## Recon page behavior

- **Capture DOM (current page)** — Calls `capture_current_page_dom()` on the **shared** Playwright session (same instance as `suno_*` / `recon_*` MCP tools). Writes `page_dom_*.html` and `page_analysis_*.json` under **`recon_output/`** (path shown in response and via `GET /api/v1/recon/output-dir`).
- **Map interactive elements** — Runs `find_interactive_elements()`; saves `interactive_elements_*.json` under `recon_output/`.

You must already have opened a session (e.g. `suno_open_browser`) and navigated to a real URL; otherwise the capture may return a “no page loaded” style message.

## Related MCP tools

- `recon_capture_page` — Same as capture-current (any page).
- `recon_capture_dom` — Studio-focused path (expects `/studio` in URL for the legacy message path; use `recon_capture_page` for create/library).

## API reference (recon)

```
POST /api/v1/recon/capture-current   → { success, message }
POST /api/v1/recon/find-elements     → { success, message }
GET  /api/v1/recon/output-dir       → { path }
```

Full OpenAPI: **`/api/docs`** on the FastAPI port.
