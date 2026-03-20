---
name: music-generation
description: Suno AI music generation and session workflows via Suno-MCP
---

# Suno-MCP — Music generation

## When to use

- Generate AI music from text prompts with optional style and lyrics.
- Automate browser sessions: open Suno, log in, generate, download MP3s.
- Studio reconnaissance: capture DOM and selectors for future automation (Premier).

## Tool map

| Goal | Tools |
|------|--------|
| Start session | `suno_open_browser`, then `suno_login` |
| Create track | `suno_generate_track` |
| Download | `suno_download_track` |
| Status | `suno_get_status`, `get_server_status` |
| Multi-step (sampling) | `agentic_suno_workflow` with explicit `available_tools` |
| Studio DOM / cookies | `recon_*` tools |

## Parameters

- **suno_generate_track**: `prompt` (required), `style` (e.g. synthwave, pop), optional `lyrics`, `duration` (auto/short/medium/long).
- **Credentials**: Never commit real passwords; use env or secure local config outside the repo.

## Agentic workflow

Use `agentic_suno_workflow` with a clear `workflow_prompt` and tool names such as:

`suno_open_browser`, `suno_login`, `suno_generate_track`, `suno_get_status`, `suno_download_track`

Requires FastMCP 3.1+ sampling (client or server-side LLM via `SUNO_SAMPLING_*`).
