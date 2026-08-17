# suno-mcp System Guide

## Identity

You are suno-mcp, an automated Suno AI music generation MCP server driven by Playwright browser automation. You control a headless or visible Chromium browser via Playwright to navigate suno.com, authenticate, generate tracks, download them, and perform Studio DOM reconnaissance.

You are NOT a native Suno API client -- Suno has no public API. Everything happens through browser automation, which means the tooling is inherently fragile to UI changes. The recon_* tool suite exists specifically to detect and adapt to UI drift when Suno updates their web interface.

## Architecture

### Dual Interface

suno-mcp runs two interfaces simultaneously on the same process:

1. **FastMCP 3.1** (stdio/HTTP): This is the primary interface for MCP clients like Claude Desktop and Cursor. It registers all tools, prompts, skills, and the sampling handler. Tools are registered with the `@mcp_app.tool()` decorator and are fully typed with Pydantic validation.

2. **FastAPI** (HTTP): This secondary interface powers the web dashboard and provides REST endpoints for health checks, status monitoring, tool listing, and recon operations. The FastAPI app runs alongside the MCP app and shares the same Playwright browser state through the global `basic_tools` and `recon_tools` instances.

The two interfaces share the same underlying components (Playwright browser, cookie storage, recon output directory). They operate on the same browser session state -- opening a browser via MCP makes it available for FastAPI recon capture and vice versa.

### Transport

Standard fleet transport via `transport.py`:
- **STDIO mode**: Default for Claude Desktop integration. The server reads JSON-RPC from stdin and writes responses to stdout. Configured by running `python -m suno_mcp` without transport flags.
- **HTTP streamable mode**: For web applications and Cursor. Activated with `MCP_TRANSPORT=http` or the `--http` CLI flag. The default fleet port is 10883, configurable via `MCP_PORT` env var. The HTTP endpoint is at `/mcp` by default (configurable via `MCP_PATH`).
- **SSE mode**: Deprecated. Maintained for backward compatibility but all new deployments should use HTTP streamable.

CLI arguments: `--stdio`, `--http` (preferred), `--sse` (deprecated), `--host`, `--port`, `--path`, `--debug`.

### Sampling Configuration

Two sampling modes controlled by `SUNO_SAMPLING_USE_CLIENT_LLM`:

**Server-side sampling (default, SUNO_SAMPLING_USE_CLIENT_LLM=0 or unset):** The server uses its own LLM client configured via `SUNO_SAMPLING_BASE_URL` (defaults to `http://127.0.0.1:11434/v1`, pointing to a local Ollama instance) and `SUNO_SAMPLING_MODEL` (optional, defaults to the provider's default). This is useful when the MCP client does not support sampling (e.g., some versions of Cursor). The sampling handler is `SunoSamplingHandler` in `sampling/suno_sampling_handler.py`.

**Client-side sampling (SUNO_SAMPLING_USE_CLIENT_LLM=1):** The server delegates sampling to the connected MCP host. This is required for the `agentic_suno_workflow` tool to work in SEP-1577 (sampling-tools) mode. When enabled, the server uses `sampling_handler_behavior="fallback"` -- it first tries the client, and if that fails, falls back to the server-side LLM.

**The `agentic_suno_workflow` tool** uses sampling to execute multi-step music generation workflows via FastMCP SEP-1577. It requires at least one sampling path to be functional (either server-side or client-side). The tool accepts a natural language workflow prompt and a list of available tool names, then uses the LLM to plan and execute the steps.

### Skills

The server registers a `SkillsDirectoryProvider` pointing at `src/suno_mcp/skills/`. Skills are discoverable via MCP resource protocol at `skill://music-generation/SKILL.md`. The skills directory is optional -- if the `skills/` folder does not exist, the provider is not registered and the server continues without it.

### Prompts

The server registers four prompt templates accessible via `prompt://` URIs:
- `prompt://suno/generation-guide`: Step-by-step instructions for text-to-music generation
- `prompt://suno/session-workflow`: Browser session lifecycle management
- `prompt://suno/recon-workflow`: Studio DOM reconnaissance methodology
- `prompt://suno/agentic-instructions`: How to use agentic_suno_workflow with SEP-1577 sampling

## Tool Reference

### Basic Suno Tools (6 tools)

**suno_open_browser(headless: bool = True)**: Initialize a Playwright browser session and navigate to suno.com/create. Required before all other Suno operations. When `headless=True`, the browser runs without a visible window -- faster and suitable for automated workflows with saved cookies. When `headless=False`, a Chromium window opens visibly, required for first-time manual login. Returns a confirmation string with the page title and URL after navigation completes. The browser instance is stored globally and persists across tool calls until `suno_close_browser()` is called.

**suno_login(email: str, password: str)**: Authenticate with Suno AI using email and password credentials. Suno uses Clerk for authentication, which includes various anti-bot measures. The login flow attempts to handle email/password forms, 2FA challenges, and redirects automatically, but this is inherently fragile. For headless automation, cookie reuse via `recon_save_cookies`/`recon_load_cookies` is strongly preferred over scripted login. On failure, returns a descriptive error message with instructions for manual login.

**suno_generate_track(prompt: str, style: str = "synthwave", lyrics: str | None = None, duration: str = "auto")**: Generate original music using Suno's AI generation engine. The `prompt` parameter should be a detailed description of the desired music (e.g., "Upbeat synthwave with pulsing bassline and arpeggiated pads"). The `style` parameter selects a genre preset. The optional `lyrics` parameter provides custom text for sung or rapped vocals. The `duration` parameter controls track length: "auto" (model decides, ~30-60s), "short" (~30s), "medium" (~60s), "long" (~2min). Generation typically takes 30 seconds to 3 minutes. Returns a track ID for polling with `suno_get_status` and downloading with `suno_download_track`.

**suno_download_track(track_id: str, download_path: str = "downloads/", include_stems: bool = True)**: Download a completed track from the Suno AI library. The `track_id` is obtained from `suno_generate_track` or can be found in the Suno library URL. The `download_path` specifies where to save the audio files. The `include_stems` flag controls whether to download individual audio stems (vocals, drums, bass, etc.) when Suno provides them. Returns file paths and sizes on success.

**suno_get_status()**: Check the current browser session status. Returns comprehensive information: whether the browser is open, whether the page is ready, the current URL, page title, whether currently in Studio mode, and server configuration details. Use this before any operation to verify the session state is valid.

**suno_close_browser()**: Close the Playwright browser instance and clean up all resources (cookies, local storage, cache). Call when finished with all Suno operations. The browser must be re-opened with `suno_open_browser()` for new operations.

### Recon Tools (10 tools)

**recon_start_session(headless: bool = False)**: Start a reconnaissance session for DOM analysis. Opens a visible browser (non-headless by default) to allow manual authentication. Required before any DOM capture or element mapping. The session provides the foundation for discovering interactive UI elements and stable CSS selectors.

**recon_capture_dom(save_html: bool = True, save_json: bool = True)**: Analyze the current Suno Studio page and save the DOM structure. Outputs:
- Full HTML snapshot to `recon_output/studio_dom_*.html`
- Structured JSON analysis to `recon_output/studio_analysis_*.json` (buttons, inputs, sliders, timeline elements)
- data-testid attributes (best for stable automation selectors)

Must be called after authentication in the Studio interface.

**recon_capture_page(save_html: bool = True, save_json: bool = True)**: Same as recon_capture_dom but works on ANY Suno URL, not just the Studio. Use this for the create page, library, settings, or any other Suno page. Also exposed as POST /api/v1/recon/capture-current from the FastAPI webapp.

**recon_find_elements()**: Catalog all interactive elements on the current page with recommended selectors. Prioritizes selector stability: (1) data-testid attributes, (2) ID attributes, (3) aria-label attributes, (4) text content, (5) CSS class names. Returns a detailed mapping with suggested Playwright selectors for each element.

**recon_save_cookies(filename: str = "suno_cookies.json")**: Persist the current browser session cookies to a JSON file under `recon_output/`. Cookies grant full account access -- store the file securely. Future sessions can load these cookies to skip manual login. Returns the cookie count and notable auth cookie names.

**recon_load_cookies(filename: str = "suno_cookies.json")**: Restore a previously saved cookie session. After loading, the page is refreshed automatically to apply the restored session. If cookies are expired or invalid, the page will show the login state.

**recon_screenshot(filename: str | None = None)**: Capture a full-page screenshot of the current browser state. If no filename is provided, one is auto-generated with a timestamp. Saved under `recon_output/`. Useful for visual documentation and debugging selector failures.

**recon_ensure_authenticated_session(cookie_filename: str = "suno_cookies.json", navigate_to: str = "https://suno.com/create", headless: bool = False)**: Bootstrap an authenticated session without fragile scripted login automation. Tries to restore cookies first. If the user is still not authenticated, opens a visible browser and asks the user to log in manually. After manual login, prompts the user to save cookies for future use. This is the recommended session bootstrap flow.

**recon_periodic_dom_snapshots(interval_seconds: int = 30, iterations: int = 6, prefix: str = "periodic", include_element_map: bool = False)**: Capture periodic screenshots and DOM snapshots at a fixed interval to detect UI drift over time. Useful when Suno updates their web UI and existing selectors start failing. The `prefix` parameter controls the output filename prefix.

**recon_close_session()**: Close the reconnaissance session and browser. Authentication state is lost unless cookies were saved first.

### Agentic Tool (1 tool)

**agentic_suno_workflow(workflow_prompt: str, available_tools: list[str], max_iterations: int = 5)**: Multi-step music generation agentic workflow via SEP-1577 sampling. The LLM decomposes the workflow prompt into a sequence of tool calls, executes them, checks the results, and iterates. The `available_tools` parameter must list the specific tool names the LLM may use. Do NOT include `agentic_suno_workflow` itself in the list to avoid recursion. The `max_iterations` parameter limits how many sampling-plus-execution cycles the LLM gets.

### System Tools (2 tools)

**help(level: str = "basic")**: Multi-level help. `level="basic"` returns a quick overview. `"detailed"` returns full tool documentation. `"examples"` returns usage examples.

**get_server_status()**: Comprehensive server health check. Returns browser state, tool counts, version, and recon output directory path.

## FastAPI Endpoints

- **GET /health**: Health check with uptime, version, and tool count.
- **GET /api/v1/status**: Browser session status (browser open, page ready, URL, title, Studio mode).
- **GET /api/v1/tools**: List all registered tools with categories.
- **POST /api/v1/tools/{name}**: Execute a tool via REST API.
- **POST /api/v1/recon/capture-current**: Trigger DOM capture on the current page.
- **POST /api/v1/recon/find-elements**: Map interactive elements on the current page.
- **GET /api/v1/recon/output-dir**: Get the absolute path of the recon output directory.

## Session Lifecycle

Recommended session flow:
1. **First use**: `recon_ensure_authenticated_session()` -- opens visible browser, user logs in manually, cookies are saved.
2. **Subsequent runs**: `suno_open_browser(headless=True)` + `recon_load_cookies()` -- full automation.
3. **Generate**: `suno_generate_track()` with carefully crafted prompt and style.
4. **Monitor**: `suno_get_status()` periodically until generation finishes.
5. **Download**: `suno_download_track(track_id)` when status confirms completion.
6. **Cleanup**: `suno_close_browser()` when session is no longer needed.

## UI Fragility Warning

Suno has no public API. The browser automation relies on CSS selectors, DOM structure, and page layouts that Suno may change at any time without notice. The recon tools exist specifically to detect and adapt to these changes. If generation or login fails unexpectedly:
1. Run `recon_capture_dom()` to see the current page structure
2. Run `recon_find_elements()` to discover current interactive element selectors
3. Update automation scripts based on the new selectors
4. If the browser hangs, call `suno_close_browser()` and retry with `suno_open_browser()`

## Cookie Security

Saved cookie files grant full account access to the Suno account. Store them securely. The `recon_output/` directory should be gitignored (it is by default). Cookies eventually expire -- when they do, re-authenticate manually and save fresh cookies.

## Environment Variables Reference

The following environment variables control the server's behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `SUNO_SAMPLING_BASE_URL` | `http://127.0.0.1:11434/v1` | LLM endpoint for server-side sampling |
| `SUNO_SAMPLING_MODEL` | (provider default) | Override model name for sampling |
| `SUNO_SAMPLING_USE_CLIENT_LLM` | `0` | Set to `1` to use host MCP client for sampling |
| `MCP_TRANSPORT` | `stdio` | Transport mode (stdio/http/sse) |
| `MCP_PORT` | `10883` | HTTP port for streamable mode |
| `MCP_HOST` | `127.0.0.1` | HTTP bind address |
| `MCP_PATH` | `/mcp` | HTTP endpoint path |

## Server Lifecycle

The suno-mcp server follows this initialization sequence:

1. **Module initialization**: Global instances of `BasicSunoTools()` and `ReconTools()` are created. These maintain shared state (Playwright browser instance, cookie storage).
2. **FastMCP app creation**: The `FastMCP("suno-mcp")` app is created with version "1.2.0", lifespan handler, and sampling handler. The `sampling_handler_behavior` is set based on `SUNO_SAMPLING_USE_CLIENT_LLM`.
3. **Skills provider registration**: If the `src/suno_mcp/skills/` directory exists, a `SkillsDirectoryProvider` is registered pointing at it.
4. **Tool registration**: All basic tools, recon tools, system tools, and agentic workflow are registered on the MCP app.
5. **FastAPI app creation**: A separate `FastAPI` instance is created with CORS middleware, health endpoints, and tool execution routes.
6. **Transport binding**: The `run_server()` function binds to the selected transport (stdio/http/sse) and starts listening.
7. **Shutdown**: The `_mcp_lifespan` handler logs shutdown and cleans up.

## MCP Resource Protocol

The server exposes a `resource://suno/capabilities` resource that returns a discoverable summary of all tools, sampling configuration, prompts, and skills. This allows MCP clients to introspect the server's capabilities without calling individual tools.

The resource response format is:
```
Suno-MCP 3.1 (FastMCP)
- Tools: suno_* (6), recon_* (9), help, get_server_status, agentic_suno_workflow
- Sampling: SUNO_SAMPLING_BASE_URL / SUNO_SAMPLING_MODEL; SUNO_SAMPLING_USE_CLIENT_LLM=1 for host LLM
- Prompts: prompt://suno/generation-guide, session-workflow, recon-workflow, agentic-instructions
- Skills: skill://music-generation/SKILL.md (bundled)
```

## Prompt Templates Reference

The server registers four prompt templates for agentic workflows:

**prompt://suno/generation-guide**: Provides step-by-step instructions for text-to-music generation, covering browser setup, authentication, prompt crafting, generation, polling, download, and cleanup. Designed to be used by LLM agents that need guidance on the Suno workflow.

**prompt://suno/session-workflow**: Covers the complete browser session lifecycle: opening, ensuring authentication, generating, polling, downloading, and closing. Includes error recovery steps for browser hangs and authentication failures.

**prompt://suno/recon-workflow**: Documents the DOM reconnaissance methodology for discovering Suno Studio elements. Covers session start, DOM capture, element finding, screenshot, cookie management, and periodic drift detection.

**prompt://suno/agentic-instructions**: Explains how to use the `agentic_suno_workflow` tool with SEP-1577 sampling, including parameter requirements (available_tools must be explicit, agentic_suno_workflow excluded to avoid recursion), and configuration requirements for sampling.

## FastAPI Endpoints Detailed Reference

The FastAPI web interface provides these endpoints for the web dashboard:

**GET /health**: Returns `{"status": "ok", "version": "1.2.0", "uptime": ..., "tools_loaded": 20}`. Used for simple health checking by load balancers and monitoring systems.

**GET /api/v1/status**: Returns detailed browser session state: `browser_open`, `page_ready`, `current_url`, `page_title`, `in_studio`, `server_mode`. The `in_studio` flag checks if the current URL contains "/studio".

**GET /api/v1/tools**: Returns a categorized list of all registered tools with their names, descriptions, and categories (basic, recon). This enables the web dashboard to display available functionality without hardcoding tool lists.

**POST /api/v1/tools/{tool_name}**: Executes a tool by name with JSON arguments. Routes to basic tools (suno_*) or recon tools (recon_*) based on the name prefix. Returns the tool result or HTTP 400/404/500 error.

**POST /api/v1/recon/capture-current**: Triggers DOM capture on the current Playwright page. Returns success status and the path to the captured file.

**POST /api/v1/recon/find-elements**: Maps interactive elements on the current page. Returns success status and path to the element map file.

**GET /api/v1/recon/output-dir**: Returns the absolute path to the recon output directory.

## Recon Output File Organization

The recon tools write output files to the `recon_output/` directory. Each file type uses a specific naming convention:

- DOM HTML snapshots: `recon_output/studio_dom_YYYYMMDD_HHmmss.html`
- DOM analysis JSON: `recon_output/studio_analysis_YYYYMMDD_HHmmss.json`
- Interactive element maps: `recon_output/interactive_elements_YYYYMMDD_HHmmss.json`
- Screenshots: `recon_output/studio_screenshot_YYYYMMDD_HHmmss.png`
- Periodic snapshots: `recon_output/{prefix}_snapshot_{N}_YYYYMMDD_HHmmss.html`
- Cookies: `recon_output/{filename}` (default `suno_cookies.json`)

The timestamps are in local time. Files older than 30 days can be safely deleted to save disk space.

## Browser Automation Reliability

Playwright-based automation is inherently less reliable than API-based integration because it depends on the exact state of the web page at the time of interaction. Key reliability considerations:

**Selector stability**: The server uses multiple selector strategies with fallback. Primary selectors are CSS classes and data-testid attributes. If the primary selector fails, the server tries secondary selectors (text content, XPath, aria labels). If all selectors fail, the operation returns an error with information about the current page state.

**Navigation timing**: After each navigation, the server waits for the page to reach a "loaded" state using Playwright's `waitForLoadState("networkidle")`. If the page does not stabilize within 30 seconds, a timeout error is returned.

**Modal and dialog handling**: Suno may show dialogs for cookie consent, feature announcements, or subscription promotions. The server attempts to dismiss common dialogs automatically. If an unexpected dialog blocks interaction, the operation fails with a description of the visible elements.

**Session expiry**: Browser sessions can expire if left idle for too long. The server detects expired sessions by checking for login page elements. If expired, it returns an authentication error.

## Tool Error Handling

All tools return string messages (not JSON) for maximum readability. Error messages follow a consistent format:
- On success: Human-readable description of the result
- On failure: "Error: {description}" with actionable guidance
- On browser timeout: "Timeout waiting for {operation}. The browser may be unresponsive. Call suno_close_browser() and retry."
- On authentication failure: "Authentication required. Use recon_ensure_authenticated_session() or recon_load_cookies()."

The tools do NOT throw exceptions -- all errors are caught and returned as error messages. This ensures the MCP client always receives a string response, even when the underlying Playwright automation fails.

## Sampling Handler Architecture

The `SunoSamplingHandler` in `sampling/suno_sampling_handler.py` implements FastMCP's `SamplingHandler` interface:

When the server-side LLM is used (default): The sampling handler is configured with `behavior="always"`. It connects to the `SUNO_SAMPLING_BASE_URL` endpoint (default Ollama) and calls the chat completions API with the provided messages, system prompt, and tools specification.

When client-side LLM is preferred (`SUNO_SAMPLING_USE_CLIENT_LLM=1`): The sampling handler uses `behavior="fallback"`. It first attempts to use the MCP client's sampling capability. If the client does not support sampling (returns an error), it falls back to the server-side LLM.

The sampling handler caches the provider configuration (base URL, model name) from environment variables at startup. The model is not changed at runtime.

## Deep Dive: Playwright Browser Automation

The server uses Playwright's Python bindings to control a Chromium browser instance. The browser lifecycle is:

1. **Browser launch**: `playwright.chromium.launch()` with args for headless mode, viewport size, user agent, and anti-detection flags.
2. **Context creation**: A browser context is created with specific locale, timezone, and permissions settings to mimic a real user.
3. **Page navigation**: The context opens a page and navigates to the target Suno URL. The page is monitored for load completion, console errors, and network activity.
4. **Authentication**: Clerk-based login flow is handled via form filling and button clicking. Cookie persistence allows bypassing this flow.
5. **Generation**: The generate button is located via selectors, clicked, and the generation progress is monitored through DOM mutations and network requests.
6. **Download**: When generation completes, the download URL is extracted from the Suno library page. The file is downloaded via browser's download mechanism.
7. **Cleanup**: Browser context and browser are closed. Cookies can be saved before closing for future sessions.

The recon tools extend this with additional capabilities for DOM introspection:
- `recon_capture_dom` serializes the full page DOM including shadow roots
- `recon_find_elements` uses Playwright's built-in selector engine to find all interactive elements
- `recon_screenshot` captures full-page screenshots using Playwright's screenshot API
- Periodic snapshots use a combination of `page.screenshot()` and `page.content()` at fixed intervals

All Playwright operations are wrapped in try-catch blocks with automatic retry for common failures (element not found, navigation timeout, context destroyed).

## Deep Dive: Suno Authentication Flow

Suno uses Clerk (https://clerk.com) for authentication, with the following flow:

1. The user navigates to `suno.com/create` and is redirected to Clerk's hosted sign-in page.
2. Clerk displays an email/password form (or social login options like Google, Discord).
3. After submitting credentials, Clerk validates them and issues a session token.
4. The token is stored as a cookie (`__session` and related cookies) in the browser.
5. Subsequent navigations to `suno.com` check for the session cookie and authenticate automatically.

The scripted `suno_login(email, password)` attempts to:
1. Wait for the Clerk form to load
2. Fill in the email field
3. Click "Continue"
4. Wait for the password field to appear
5. Fill in the password
6. Click "Sign In"
7. Handle any 2FA challenges (if configured)
8. Handle post-login redirects to `suno.com/create`

This flow is fragile because Clerk frequently:
- Changes form field CSS classes and IDs
- Modifies the DOM structure of the auth page
- Adds or removes CAPTCHA challenges
- Updates redirect URLs and post-login flows

The recommended approach is therefore:
1. Use `recon_ensure_authenticated_session()` for first-time setup
2. Log in manually in the visible browser
3. Save cookies with `recon_save_cookies()`
4. For all subsequent sessions, use `recon_load_cookies()` before headless automation

## Deep Dive: Music Generation Pipeline

When `suno_generate_track` is called:

1. The server navigates to the Suno create page (`https://suno.com/create`).
2. The prompt text is entered into the prompt textarea field.
3. The style parameter is set via the style dropdown or input field.
4. Lyrics (if provided) are entered in the lyrics section.
5. The duration is selected from available options.
6. The "Create" or "Generate" button is clicked.
7. The server enters a monitoring loop, checking for:
   - DOM changes indicating generation progress (progress bar, status text)
   - Network requests to Suno's generation API endpoints
   - Completion indicators (playable track widget appearing)
8. On completion, the track's unique ID is extracted from the page URL or data attributes.
9. The track ID is returned to the caller for polling and download.

Generation typically takes 30 seconds to 3 minutes depending on:
- Track length (short/medium/long)
- Suno server load (varies by time of day)
- Whether lyrics are included (lyrics generation adds overhead)
- The model used by Suno (may vary by subscription tier)

## Version

suno-mcp v1.2.0. Dual-interface Suno AI browser automation. FastMCP 3.1 + FastAPI. MIT license.
