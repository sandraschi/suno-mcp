# suno-mcp (MCPB Bundle)

MCP server: Playwright automation against suno.com (fragile); DOM recon tools; no official Suno API

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "suno-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "suno_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **suno_open_browser**: suno_open_browser
- **suno_login**: suno_login
- **suno_generate_track**: suno_generate_track
- **suno_download_track**: suno_download_track
- **suno_get_status**: suno_get_status
- **suno_close_browser**: suno_close_browser
- **recon_start_session**: recon_start_session
- **recon_capture_dom**: recon_capture_dom
- **recon_capture_page**: recon_capture_page
- **recon_find_elements**: recon_find_elements
- **recon_save_cookies**: recon_save_cookies
- **recon_load_cookies**: recon_load_cookies
- **recon_screenshot**: recon_screenshot
- **recon_ensure_authenticated_session**: recon_ensure_authenticated_session
- **recon_periodic_dom_snapshots**: recon_periodic_dom_snapshots
- **recon_close_session**: recon_close_session
- **help**: help
- **get_server_status**: get_server_status
- **list_tools**: List all available tools via FastAPI.
- **api_recon_output_dir**: Absolute path to the directory where recon HTML/JSON is written (cwd-relative).
- **execute_tool**: Execute a tool via FastAPI.
- **main_stdio**: main(stdio)
- **main_http**: main(http)
- **main_sse**: main(sse)
- **agentic_suno_workflow**: agentic_suno_workflow

## Requirements

- Python 3.12+
- uv
