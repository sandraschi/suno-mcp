# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Shared Playwright session:** `suno_*` and `recon_*` tools now use one `BrowserManager` via `get_shared_browser_manager()` so human-in-the-loop uses a single Chromium window instead of two independent instances.

### Documentation
- README: clarify what “human-in-the-loop” means (Playwright only), what MCP/FastAPI/web_sota actually do, and how to improve the stack.

### Fixed
- **web_sota:** Dashboard and Status pages now load **real** `GET /health` and `GET /api/v1/status` instead of hard-coded KPIs; added `src/lib/backend.ts`, `VITE_API_BASE_URL`, `src/vite-env.d.ts`. Build fixes (unused imports, `Music` icon).

### Added
- **`recon_capture_page` MCP tool** and **`capture_current_page_dom`** (any Suno URL, not only `/studio`).
- **FastAPI:** `POST /api/v1/recon/capture-current`, `POST /api/v1/recon/find-elements`, `GET /api/v1/recon/output-dir`.
- **web_sota:** `/recon` page with buttons to run capture + element map against the live Playwright session.
- **HTTP tool executor:** `recon_close_session`, `recon_ensure_authenticated_session`, `recon_periodic_dom_snapshots` wired in `_handle_recon_tool` (were missing before).

## [1.2.0] - 2026-03-20

### Added
- **FastMCP 3.1**: `from fastmcp import FastMCP` with `instructions`, lifespan, `on_duplicate="replace"`.
- **Sampling**: `SunoSamplingHandler` — OpenAI-compatible chat/completions (default local Ollama); env `SUNO_SAMPLING_*`, `SUNO_SAMPLING_USE_CLIENT_LLM`.
- **Prompts**: `prompt://suno/generation-guide`, `session-workflow`, `recon-workflow`, `agentic-instructions`.
- **Skills**: `SkillsDirectoryProvider` — bundled `skills/music-generation/SKILL.md` (`skill://music-generation/SKILL.md`).
- **Agentic workflow**: `agentic_suno_workflow` (SEP-1577) — `context.sample_step` loop with selected tools.
- **Resource**: `resource://suno/capabilities`.
- **Dependencies**: `httpx` (sampling HTTP), `fastmcp>=3.1.0,<4`.

### Fixed
- **Entry points**: `main()` now passes `mcp_app` to `run_server` (was incorrectly passing `get_server_status`). `main_api()` uses `uvicorn.run(fastapi_app, ...)` instead of misusing `run_server`.

### Changed
- Version 1.2.0 across package, FastAPI, and help text; tool count includes `agentic_suno_workflow` (17 tools).

## [1.1.0] - 2025-11-28

### Added
- **Reconnaissance Tools (7 new tools)**: DOM analysis for Studio automation development
  - `recon_start_session(headless)` - Start visible browser for manual Suno login
  - `recon_capture_dom(save_html, save_json)` - Capture Studio DOM structure
  - `recon_find_elements()` - Map interactive UI elements with stable selectors
  - `recon_save_cookies(filename)` - Preserve authenticated session
  - `recon_load_cookies(filename)` - Restore session without re-login
  - `recon_screenshot(filename)` - Visual documentation capture
  - `recon_close_session()` - Clean browser shutdown

### Features
- **DOM Analysis**: Automatic extraction of buttons, inputs, sliders, timeline elements
- **Selector Priority**: Prefers data-testid > id > aria-label > text > class
- **Cookie Persistence**: Save/restore auth sessions for headless automation
- **Element Mapping**: JSON export of interactive elements with suggested selectors
- **Screenshot Capture**: Full-page screenshots for visual reference

### Technical
- New `tools/recon/` module with `ReconTools` class
- Updated server.py with 7 new MCP tool registrations
- Added FastAPI routing for recon tools (`_handle_recon_tool`)
- Output directory: `recon_output/` for all captured data
- Added fastapi and uvicorn to dependencies

### Changed
- Version bump to 1.1.0
- Updated help system with recon tool documentation
- Tool count updated: 16 total (6 basic + 7 recon + 3 system)

---

## [1.0.0] - 2025-01-27

### Added
- **Complete MCP Architecture**: Dual interface support (MCP + FastAPI)
- **24 MCP Tools**: 6 basic Suno AI tools + 18 Suno Studio beta tools
- **FastAPI Endpoints**:
  - `/health` - Health check endpoint
  - `/api/docs` - OpenAPI documentation
  - `/api/v1/tools` - Tool listing
  - `/api/v1/status` - Server status
  - `/api/v1/tools/:name` - Tool execution
- **Browser Automation**: Playwright-powered Suno AI interaction
- **Comprehensive Documentation**: Complete technical documentation suite
- **Testing Framework**: Jest unit tests + PowerShell local tests
- **Production Checklist**: MCP server production readiness audit

### Features
- **Basic Suno AI Integration**:
  - Browser automation for Suno AI platform
  - Automated login and authentication
  - Track generation from text prompts
  - Download management with stems support
  - Real-time status monitoring

- **Suno Studio Beta Support**:
  - Project management (create, open, save)
  - AI stem generation (vocals, drums, bass, synths)
  - Timeline manipulation and arrangement
  - BPM and tempo control
  - Volume adjustment and effects
  - Advanced export capabilities
  - Real-time generation monitoring

- **Developer Experience**:
  - Dual interface (stdio MCP + HTTP FastAPI)
  - Comprehensive error handling
  - Session persistence
  - Cross-platform support (Windows/macOS/Linux)
  - Claude Desktop integration

### Technical
- **Dependencies**: Added FastAPI, Playwright, Jest testing
- **Architecture**: Modular dual-interface server
- **Testing**: Unit tests, integration tests, local PowerShell tests
- **Documentation**: PRD, technical specs, API docs
- **CI/CD Ready**: GitHub Actions workflows prepared

### Known Issues
- Suno Studio tools are placeholder implementations
- Requires Suno Premier subscription for full functionality
- Some advanced features need real Playwright automation

---

## Development Status

### ✅ Completed (Phase 1)
- [x] MCP server architecture with dual interfaces
- [x] 24 tool definitions with proper schemas
- [x] FastAPI endpoints with OpenAPI support
- [x] Basic browser automation framework
- [x] Testing infrastructure (Jest + PowerShell)
- [x] Comprehensive documentation
- [x] Production checklist compliance

### 🔄 In Progress (Phase 2)
- [ ] Suno Studio Playwright automation implementation
- [ ] Real tool functionality (vs placeholder responses)
- [ ] Enhanced error handling and recovery
- [ ] Session persistence and management
- [ ] Advanced testing and validation

### 📋 Planned (Phase 3-6)
- [ ] Full Suno Studio beta integration
- [ ] Timeline manipulation tools
- [ ] Advanced mixing and effects
- [ ] Batch processing workflows
- [ ] Performance optimization
- [ ] Production deployment

---

## Contributing

This project follows semantic versioning. For changes that affect the public API or tool interfaces, please update the version accordingly.

### Types of Changes
- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** in case of vulnerabilities

---

*This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.*
