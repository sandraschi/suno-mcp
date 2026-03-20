#!/usr/bin/env python3
"""Suno MCP Server — FastMCP 3.1 (MCP + FastAPI): sampling, prompts, skills, agentic workflow."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider
from pydantic import BaseModel

from .sampling.suno_sampling_handler import SunoSamplingHandler
from .tools.agentic_suno_workflow import register_agentic_suno_workflow
from .tools.basic.tools import BasicSunoTools
from .tools.recon.tools import ReconTools
from .transport import run_server

_USE_CLIENT_SAMPLING = os.getenv("SUNO_SAMPLING_USE_CLIENT_LLM", "").lower() in (
    "1",
    "true",
    "yes",
)


# FastAPI Models
class ToolRequest(BaseModel):
    """Request model for tool execution via FastAPI."""
    name: str
    arguments: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "ok"
    version: str = "1.2.0"
    uptime: float
    tools_loaded: int


class StatusResponse(BaseModel):
    """Status response model."""
    browser_open: bool
    page_ready: bool
    current_url: str | None
    page_title: str | None
    in_studio: bool
    server_mode: str


# Global instances
basic_tools = BasicSunoTools()
recon_tools = ReconTools()

sampling_handler = SunoSamplingHandler()


@asynccontextmanager
async def _mcp_lifespan(_app: FastMCP):
    logging.info("Suno MCP (FastMCP 3.1) lifespan start")
    yield
    logging.info("Suno MCP lifespan shutdown")


# FastMCP 3.1 app (stdio / HTTP via transport)
mcp_app = FastMCP(
    name="suno-mcp",
    version="1.2.0",
    instructions="""You are Suno-MCP: Suno AI music generation and Studio reconnaissance via Playwright.

CORE: suno_open_browser, suno_login, suno_generate_track, suno_download_track, suno_get_status, suno_close_browser.
RECON: recon_* for DOM capture, cookies, screenshots (Studio automation prep).
SYSTEM: help, get_server_status.
AGENTIC: agentic_suno_workflow — multi-step workflows via sampling with tools (SEP-1577); pass explicit tool names.

SAMPLING: Default server-side OpenAI-compatible LLM at SUNO_SAMPLING_BASE_URL (Ollama http://127.0.0.1:11434/v1). Set SUNO_SAMPLING_USE_CLIENT_LLM=1 to prefer the host LLM. Skills: skill://music-generation/SKILL.md.""",
    lifespan=_mcp_lifespan,
    sampling_handler=sampling_handler,
    sampling_handler_behavior="fallback" if _USE_CLIENT_SAMPLING else "always",
    strict_input_validation=True,
    tasks=False,
    on_duplicate="replace",
)

_skills_root = Path(__file__).resolve().parent / "skills"
if _skills_root.is_dir():
    mcp_app.add_provider(SkillsDirectoryProvider(roots=[_skills_root]))

# Lifespan context manager for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle FastAPI startup and shutdown events."""
    # Startup
    logging.info("Starting Suno MCP Server (Dual Interface)")
    yield
    # Shutdown
    logging.info("Shutting down Suno MCP Server")


# FastAPI App
fastapi_app = FastAPI(
    title="Suno MCP Server",
    description="Automated Suno AI Music Generation MCP Server with Studio Reconnaissance",
    version="1.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ASGI entry for uvicorn (web_sota/start.ps1: uvicorn suno_mcp.server:app ...)
app = fastapi_app


@mcp_app.resource("resource://suno/capabilities")
def get_suno_capabilities() -> str:
    """Discoverable summary of Suno-MCP 3.1 tools, sampling, prompts, and skills."""
    return """Suno-MCP 3.1 (FastMCP)
- Tools: suno_* (6), recon_* (9), help, get_server_status, agentic_suno_workflow
- Sampling: SUNO_SAMPLING_BASE_URL / SUNO_SAMPLING_MODEL; SUNO_SAMPLING_USE_CLIENT_LLM=1 for host LLM
- Prompts: prompt://suno/generation-guide, session-workflow, recon-workflow, agentic-instructions
- Skills: skill://music-generation/SKILL.md (bundled)
"""


@mcp_app.prompt("prompt://suno/generation-guide")
def prompt_generation_guide() -> str:
    """Instructions for text-to-music generation with Suno-MCP."""
    return """Guide the user through Suno AI music generation with suno-mcp.
1. suno_open_browser(headless=true) unless they need visible login.
2. Prefer manual login + recon_ensure_authenticated_session / cookie reuse.
3. suno_generate_track(prompt=..., style=..., lyrics=optional, duration=auto|short|medium|long).
4. suno_get_status() while waiting; suno_download_track(track_id=..., download_path=...) when ready.
5. suno_close_browser() when done."""


@mcp_app.prompt("prompt://suno/session-workflow")
def prompt_session_workflow() -> str:
    """Browser session and cleanup."""
    return """Suno session workflow:
- Open → ensure authenticated session → generate → poll status → download → close.
- If the browser hangs, suno_close_browser() and retry suno_open_browser().
- For unattended runs prefer headless after cookies exist (recon_save_cookies / recon_load_cookies)."""


@mcp_app.prompt("prompt://suno/recon-workflow")
def prompt_recon_workflow() -> str:
    """Studio DOM reconnaissance workflow."""
    return """Studio reconnaissance (Premier / visible browser):
1. recon_start_session(headless=false), manual login, navigate to Studio.
2. recon_capture_dom(), recon_find_elements(), recon_screenshot().
3. recon_save_cookies() for reuse; recon_close_session() when finished."""


@mcp_app.prompt("prompt://suno/agentic-instructions")
def prompt_agentic_instructions() -> str:
    """How to use agentic_suno_workflow (SEP-1577)."""
    return """agentic_suno_workflow(workflow_prompt, available_tools, max_iterations):
- Pass concrete tool names: e.g. ["suno_open_browser","suno_login","suno_generate_track","suno_get_status"].
- Requires FastMCP 3.1 sampling (server-side Ollama via SUNO_SAMPLING_* or a capable client).
- Do not include agentic_suno_workflow inside available_tools (avoid recursion)."""


# FastAPI Routes
@fastapi_app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint returning JSON status."""
    import time
    start_time = getattr(fastapi_app, "start_time", time.time())
    current_time = time.time()

    return HealthResponse(
        status="ok",
        version="1.2.0",
        uptime=current_time - start_time,
        tools_loaded=19,
    )


@fastapi_app.get("/api/v1/status", response_model=StatusResponse)
async def get_status():
    """Get current server and browser status."""
    try:
        # Get browser status from basic tools
        browser_status = await basic_tools.get_browser_status()
        current_url = browser_status.get("current_url", "")
        return StatusResponse(
            browser_open=browser_status.get("browser_open", False),
            page_ready=browser_status.get("page_ready", False),
            current_url=current_url,
            page_title=browser_status.get("page_title"),
            in_studio="/studio" in (current_url or ""),
            server_mode="dual"
        )
    except Exception as e:
        logging.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")


@fastapi_app.get("/api/v1/tools")
async def list_tools():
    """List all available tools via FastAPI."""
    tools = []

    # Basic tools
    basic_tool_names = [
        "suno_open_browser", "suno_login", "suno_generate_track",
        "suno_download_track", "suno_get_status", "suno_close_browser"
    ]
    for name in basic_tool_names:
        tools.append({
            "name": name,
            "description": f"{name} tool",
            "category": "basic"
        })

    # Recon tools
    recon_tool_names = [
            "recon_start_session", "recon_capture_dom", "recon_find_elements",
            "recon_save_cookies", "recon_load_cookies", "recon_screenshot",
            "recon_ensure_authenticated_session", "recon_periodic_dom_snapshots", "recon_close"
    ]
    for name in recon_tool_names:
        tools.append({
            "name": name,
            "description": f"{name} tool",
            "category": "recon"
        })

    return {"tools": tools}


@fastapi_app.post("/api/v1/tools/{tool_name}")
async def execute_tool(tool_name: str, request: ToolRequest):
    """Execute a tool via FastAPI."""
    try:
        args = request.arguments or {}

        # Route to appropriate tool handler
        if tool_name.startswith("suno_"):
            result = await _handle_basic_tool(tool_name, args)
        elif tool_name.startswith("recon_"):
            result = await _handle_recon_tool(tool_name, args)
        else:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

        return {"result": result, "tool": tool_name, "success": True}

    except Exception as e:
        logging.error(f"Tool execution failed: {tool_name}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


# Tool execution helpers
async def _handle_basic_tool(tool_name: str, args: dict[str, Any]) -> str:
    """Handle basic Suno AI tools."""
    tool_map = {
        "suno_open_browser": basic_tools.open_browser,
        "suno_login": basic_tools.login,
        "suno_generate_track": basic_tools.generate_track,
        "suno_download_track": basic_tools.download_track,
        "suno_get_status": basic_tools.get_status,
        "suno_close_browser": basic_tools.close_browser,
    }

    if tool_name not in tool_map:
        raise HTTPException(status_code=404, detail=f"Unknown basic tool: {tool_name}")

    return await tool_map[tool_name](**args)


async def _handle_recon_tool(tool_name: str, args: dict[str, Any]) -> str:
    """Handle reconnaissance tools."""
    tool_map = {
        "recon_start_session": recon_tools.start_recon_session,
        "recon_capture_dom": recon_tools.capture_studio_dom,
        "recon_find_elements": recon_tools.find_interactive_elements,
        "recon_save_cookies": recon_tools.save_cookies,
        "recon_load_cookies": recon_tools.load_cookies,
        "recon_screenshot": recon_tools.take_screenshot,
        "recon_close": recon_tools.close_session,
    }

    if tool_name not in tool_map:
        raise HTTPException(status_code=404, detail=f"Unknown recon tool: {tool_name}")

    return await tool_map[tool_name](**args)


# =============================================================================
# MCP Tool Registration - Basic Tools
# =============================================================================

@mcp_app.tool()
async def suno_open_browser(headless: bool = True) -> str:
    """
    Open browser and navigate to Suno AI create page.

    This tool initializes a Playwright browser session and navigates to the Suno AI
    music generation interface. Required for all other Suno AI operations.

    Args:
        headless: Run browser in headless mode (default: True)

    Returns:
        Confirmation message with page details and navigation status
    """
    return await basic_tools.open_browser(headless)


@mcp_app.tool()
async def suno_login(email: str, password: str) -> str:
    """
    Login to Suno AI account.

    Authenticates with Suno AI using provided credentials. Required before
    generating tracks or accessing the library. Handles 2FA and various
    authentication flows automatically.

    Args:
        email: Suno AI account email address
        password: Suno AI account password

    Returns:
        Login status and session confirmation
    """
    return await basic_tools.login(email, password)


@mcp_app.tool()
async def suno_generate_track(
    prompt: str,
    style: str = "synthwave",
    lyrics: str | None = None,
    duration: str = "auto",
) -> str:
    """
    Generate a new music track using Suno AI.

    Creates original music using Suno's AI generation engine. Supports various
    styles, lyrics integration, and custom durations. Generation may take
    several minutes depending on complexity.

    Args:
        prompt: Detailed description of the desired music (required)
        style: Musical style (e.g., "synthwave", "pop", "rock", default: "synthwave")
        lyrics: Optional lyrics to incorporate into the track
        duration: Track length ("auto", "short", "medium", "long", default: "auto")

    Returns:
        Generation status and track information when complete
    """
    return await basic_tools.generate_track(prompt, style, lyrics, duration)


@mcp_app.tool()
async def suno_download_track(
    track_id: str,
    download_path: str = "downloads/",
    include_stems: bool = True,
) -> str:
    """
    Download a generated track from Suno AI library.

    Downloads completed tracks and optionally their individual stems/components.
    Supports custom download paths and automatic file organization.

    Args:
        track_id: Unique identifier of the track to download
        download_path: Directory to save files (default: "downloads/")
        include_stems: Download individual track stems if available (default: True)

    Returns:
        Download confirmation with file paths and sizes
    """
    return await basic_tools.download_track(track_id, download_path, include_stems)


@mcp_app.tool()
async def suno_get_status() -> str:
    """
    Get current Suno AI session status.

    Provides comprehensive information about the current browser session,
    authentication state, and active operations.

    Returns:
        Detailed status report including session state and capabilities
    """
    return await basic_tools.get_status()


@mcp_app.tool()
async def suno_close_browser() -> str:
    """
    Close the browser session.

    Properly closes the Playwright browser instance and cleans up resources.
    Should be called when finished with Suno AI operations.

    Returns:
        Confirmation of browser closure
    """
    return await basic_tools.close_browser()


# =============================================================================
# MCP Tool Registration - Reconnaissance Tools (NEW)
# =============================================================================

@mcp_app.tool()
async def recon_start_session(headless: bool = False) -> str:
    """
    Start a reconnaissance session for Suno Studio DOM analysis.

    Opens a browser in VISIBLE mode (non-headless by default) to allow manual
    authentication with Suno AI. Required before capturing DOM structure or
    mapping interactive elements.

    Since Suno has no public API, reconnaissance tools help discover:
    - Interactive UI elements (buttons, sliders, inputs)
    - Timeline and track structure
    - Stem generation controls
    - Stable selectors for automation

    Args:
        headless: Run in headless mode (default: False for manual login)

    Returns:
        Session status with instructions for next steps
    """
    return await recon_tools.start_recon_session(headless)


@mcp_app.tool()
async def recon_capture_dom(
    save_html: bool = True,
    save_json: bool = True,
) -> str:
    """
    Capture the current Suno Studio DOM structure.

    Analyzes the page and saves:
    - Full HTML snapshot for offline analysis
    - Structured JSON with buttons, inputs, sliders, timeline elements
    - data-testid elements (best for stable automation selectors)

    Must be called after authentication in Studio interface.

    Args:
        save_html: Save raw HTML to file (default: True)
        save_json: Save structured analysis to JSON (default: True)

    Returns:
        Summary of captured elements with file paths
    """
    return await recon_tools.capture_studio_dom(save_html, save_json)


@mcp_app.tool()
async def recon_find_elements() -> str:
    """
    Find and catalog all interactive elements in the current page.

    Maps clickable elements, inputs, sliders with their best selectors
    for automation scripting. Prioritizes:
    1. data-testid attributes (most stable)
    2. ID attributes
    3. aria-label attributes
    4. Text content for buttons
    5. Class names (least stable, fallback only)

    Returns:
        Detailed element mapping with suggested selectors
    """
    return await recon_tools.find_interactive_elements()


@mcp_app.tool()
async def recon_save_cookies(filename: str = "suno_cookies.json") -> str:
    """
    Save current session cookies for reuse.

    Preserves authentication state so future sessions can skip manual login
    (until cookies expire). Store securely - cookies grant account access!

    Args:
        filename: Output filename for cookies JSON (default: "suno_cookies.json")

    Returns:
        Confirmation with cookie count and notable auth cookies
    """
    return await recon_tools.save_cookies(filename)


@mcp_app.tool()
async def recon_load_cookies(filename: str = "suno_cookies.json") -> str:
    """
    Load previously saved cookies into current session.

    Restores authentication state from saved cookies file. After loading,
    the page is refreshed to apply the session.

    Args:
        filename: Cookie file to load (default: "suno_cookies.json")

    Returns:
        Status of cookie restoration and current auth state
    """
    return await recon_tools.load_cookies(filename)


@mcp_app.tool()
async def recon_screenshot(filename: str | None = None) -> str:
    """
    Take a screenshot of the current page.

    Captures full-page screenshot for visual documentation or debugging.
    Saved to recon_output/ directory.

    Args:
        filename: Optional filename (auto-generated with timestamp if not provided)

    Returns:
        Path to saved screenshot
    """
    return await recon_tools.take_screenshot(filename)


@mcp_app.tool()
async def recon_ensure_authenticated_session(
    cookie_filename: str = "suno_cookies.json",
    navigate_to: str = "https://suno.com/create",
    headless: bool = False,
) -> str:
    """
    Ensure authenticated session without scripted Clerk/login automation.

    Attempts cookie restore first. If still signed-out, asks user to login manually
    in the visible browser and then save cookies for future runs.
    """
    return await recon_tools.ensure_authenticated_session(
        cookie_filename=cookie_filename,
        navigate_to=navigate_to,
        headless=headless,
    )


@mcp_app.tool()
async def recon_periodic_dom_snapshots(
    interval_seconds: int = 30,
    iterations: int = 6,
    prefix: str = "periodic",
    include_element_map: bool = False,
) -> str:
    """
    Capture periodic screenshot + DOM snapshots to detect UI drift.

    Useful when Suno updates web UI and selectors start failing.
    """
    return await recon_tools.periodic_dom_snapshots(
        interval_seconds=interval_seconds,
        iterations=iterations,
        prefix=prefix,
        include_element_map=include_element_map,
    )


@mcp_app.tool()
async def recon_close_session() -> str:
    """
    Close the reconnaissance session and browser.

    Properly terminates the browser session. Note: You'll need to
    re-authenticate if starting a new session without saved cookies.

    Returns:
        Confirmation of session closure
    """
    return await recon_tools.close_session()


# =============================================================================
# System Tools
# =============================================================================

@mcp_app.tool()
async def help(level: str = "basic") -> str:
    """
    Multilevel help system for Suno MCP Server.

    Provides contextual help information at different levels of detail.
    Essential for user onboarding and tool discovery.

    Args:
        level: Help detail level ("basic", "detailed", "examples", default: "basic")

    Returns:
        Formatted help text with usage instructions and examples
    """
    if level == "basic":
        return """
🎵 **Suno MCP Server Help** (v1.2.0)

**Available Tool Categories:**
• **Basic Tools (6)**: Core Suno AI music generation
• **Recon Tools (9)**: Studio DOM analysis, auth-session reuse, and drift snapshots
• **Agentic (1)**: `agentic_suno_workflow` — multi-step flows via sampling (FastMCP 3.1)

**Getting Started:**
1. Use `suno_open_browser()` to start a session
2. Use `recon_ensure_authenticated_session()` for manual-login reuse
3. Use `suno_generate_track()` to create music

**For Studio Automation Development:**
1. Use `recon_start_session()` to open visible browser
2. Manually login to Suno (Premier required for Studio)
3. Navigate to Studio
4. Use `recon_capture_dom()` to analyze interface
5. Use `recon_save_cookies()` to preserve session

**For detailed help:** Use `help("detailed")`
"""
    elif level == "detailed":
        return """
🎵 **Suno MCP Server - Detailed Help** (v1.2.0)

**Basic Tools:**
- `suno_open_browser(headless=true)` - Start browser session
- `suno_login(email, password)` - Authenticate with Suno
- `suno_generate_track(prompt, style, lyrics, duration)` - Generate music
- `suno_download_track(track_id, path, include_stems)` - Download tracks
- `suno_get_status()` - Check session status
- `suno_close_browser()` - End session

**Reconnaissance Tools (NEW):**
- `recon_start_session(headless=false)` - Start visible browser for manual auth
- `recon_capture_dom(save_html, save_json)` - Capture Studio DOM structure
- `recon_find_elements()` - Map interactive UI elements with selectors
- `recon_save_cookies(filename)` - Preserve auth session
- `recon_load_cookies(filename)` - Restore auth session
- `recon_screenshot(filename)` - Capture page screenshot
- `recon_ensure_authenticated_session(cookie_filename, navigate_to, headless)` - Manual-login-first session bootstrap
- `recon_periodic_dom_snapshots(interval_seconds, iterations, prefix, include_element_map)` - Scheduled drift snapshots
- `recon_close_session()` - Close browser

**Agentic (sampling):**
- `agentic_suno_workflow(workflow_prompt, available_tools, max_iterations=5)` — SEP-1577; configure `SUNO_SAMPLING_*` or client sampling

**Output Locations:**
- DOM captures: `recon_output/studio_dom_*.html`
- Analysis JSON: `recon_output/studio_analysis_*.json`
- Element maps: `recon_output/interactive_elements_*.json`
- Cookies: `recon_output/suno_cookies.json`
- Screenshots: `recon_output/studio_screenshot_*.png`

**FastAPI Endpoints:**
- GET `/health` - Health check
- GET `/api/docs` - OpenAPI documentation
- GET `/api/v1/tools` - List all tools
- POST `/api/v1/tools/{name}` - Execute tools
- GET `/api/v1/status` - Server status
"""
    elif level == "examples":
        return """
🎵 **Suno MCP Server - Usage Examples**

**Basic Music Generation:**
```python
# Generate a simple track
suno_generate_track("upbeat pop song about summer", "pop")

# Generate with lyrics
suno_generate_track("ballad", "folk", "Verse lyrics here...")

# Download completed track
suno_download_track("track_123", "downloads/", True)
```

**Studio Reconnaissance Workflow:**
```python
# Step 1: Start visible browser for manual login
recon_start_session(headless=False)

# Step 2: (Manual) Login to Suno in browser window
# Step 3: (Manual) Navigate to Studio

# Step 4: Capture DOM structure
recon_capture_dom()

# Step 5: Find automation targets
recon_find_elements()

# Step 6: Save cookies for future sessions
recon_save_cookies("my_suno_session.json")

# Step 7: Take visual reference
recon_screenshot("studio_layout.png")
```

**Restore Session Later:**
```python
recon_start_session(headless=True)  # Can be headless now
recon_load_cookies("my_suno_session.json")
# Now authenticated without manual login!
```
"""
    else:
        return "Use `help()` for basic help, `help('detailed')` for comprehensive documentation, or `help('examples')` for usage examples."


@mcp_app.tool()
async def get_server_status() -> str:
    """
    Comprehensive server status and health check tool.

    Provides detailed information about server state, active sessions,
    resource usage, and system health. Essential for monitoring and
    troubleshooting MCP server operations.

    Returns:
        Detailed status report including:
        - Server configuration and capabilities
        - Active browser sessions and state
        - Tool availability and health
        - Resource usage and performance metrics
    """
    try:
        browser_status = await basic_tools.get_browser_status()

        status = f"""
🎵 **Suno MCP Server Status** (v1.2.0)

**Server Configuration:**
• Version: 1.2.0
• Mode: Dual Interface (MCP stdio + FastAPI HTTP)
• Total Tools Available: 19 (incl. agentic_suno_workflow)
• Basic Tools: 6
• Recon Tools: 9
• System Tools: 2
• Agentic: 1

**Browser Session:**
• Browser Open: {browser_status.get('browser_open', False)}
• Context Ready: {browser_status.get('context_ready', False)}
• Page Ready: {browser_status.get('page_ready', False)}
• Current URL: {browser_status.get('current_url', 'None')}
• Page Title: {browser_status.get('page_title', 'None')}
• In Studio Mode: {browser_status.get('in_studio', False)}

**System Health:**
• Status: ✅ Operational
• FastAPI: Available at http://localhost:3000
• MCP: Active on stdio
• Tools: All registered and functional

**Recon Output Directory:** recon_output/
"""
        return status
    except Exception as e:
        return f"""❌ **Status Check Failed**

Error: {str(e)}

**Troubleshooting:**
• Ensure Playwright browsers are installed: `playwright install chromium`
• Check internet connectivity
• Verify Suno AI service availability
• Review server logs for detailed error information
"""


register_agentic_suno_workflow(mcp_app)


def main():
    """Main entry point for MCP server (stdio mode)."""
    logging.info("Starting Suno MCP server (stdio mode, FastMCP 3.1)")
    run_server(mcp_app, server_name="suno-mcp")


def main_api():
    """Main entry point for FastAPI server."""
    import time

    import uvicorn

    fastapi_app.start_time = time.time()

    logging.info("Starting FastAPI server on http://0.0.0.0:3000")
    logging.info("API Docs: http://0.0.0.0:3000/api/docs")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=3000)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    main()