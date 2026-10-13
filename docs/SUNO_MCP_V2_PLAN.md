# suno-mcp v2 plan

**Status:** Phase 2 in progress (2026-10-13)

## North star

MCP control plane for Suno generation using the user's account via **paperfoot/suno-cli** (subprocess), not DOM automation.

Canonical memops note: Advanced Memory `projects/suno-mcp-v2-plan`.

## Background (reassessment summary)

| Source | Stars (approx.) | Freshness | Role |
|--------|----------------:|-----------|------|
| gcui-art/suno-api | 3,213 | Last commit 2026-03; captcha/auth forks | Self-hosted REST + Playwright |
| SunoAI-API/Suno-API | 1,810 | Stale 2025-04 | FoxAIHub-oriented FastAPI |
| paperfoot/suno-cli | 48 | Active through v0.9.0 (2026-07) | **Primary v2 engine** |
| Malith / imyizhang Python | 48-129 | 2024 chirp-v3 | Legacy |

Suno official: no public generation API (C2PA detect only); partner API intake July 2026 only.

## Architecture

```
Cursor / Claude / web_sota
        -> FastMCP + FastAPI (suno-mcp)
        -> SunoCliBackend (async subprocess)
        -> `suno` binary (paperfoot/suno-cli)
        -> studio-api-prod.suno.com

Optional: SUNO_BACKEND=playwright + SUNO_ENABLE_RECON=1 (legacy)
```

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `SUNO_BACKEND` | `cli` | `cli` or `playwright` |
| `SUNO_CLI_PATH` | `suno` | Path to paperfoot CLI |
| `SUNO_CLI_MIN_VERSION` | `0.9.0` | Warn if below (best-effort parse) |
| `SUNO_DOWNLOAD_DIR` | `downloads` | `--download` target for generate |
| `SUNO_ENABLE_RECON` | unset | Enable Playwright recon tools |

## Phases

### Phase 0 - Decision doc

- [x] `docs/SUNO_MCP_V2_PLAN.md`
- [x] `docs/UNOFFICIAL.md`
- [x] memops plan note

### Phase 1 - SunoCliBackend


- [x] `src/suno_mcp/backends/config.py`
- [x] `src/suno_mcp/backends/cli_runner.py`
- [x] `src/suno_mcp/tools/cli/tools.py`
- [x] MCP tools: `suno_auth_status`, `suno_generate`, `suno_describe`, `suno_write_scaffold`
- [x] Unit tests with mocked subprocess
- [x] FastAPI tool list + execute routes for CLI tools
- [x] FastAPI `/api/v1/status` CLI branch (credits probe)

### Phase 2 - Surface cleanup (current)

- [x] Default help points to CLI tools
- [x] `web_sota` status panel for CLI (`cli_ready`, credits)
- [x] README v2 section
- [x] Optional dependency group `legacy` (playwright duplicated for future slim default)
- [x] `scripts/doctor.ps1` (+ `just doctor`)
- [x] Deprecation note on `suno_open_browser` (pattern for other legacy tools)

### Phase 3 - Optional second backend

- Sidecar gcui fork HTTP OR reseller (`TT-API-KEY`) as separate tool namespace

### Phase 4 - Packaging

- MCPB bundles pinned `suno-cli` Windows binary
- `just doctor` runs `suno doctor` + MCP health

## CLI bootstrap (operator)

1. Install from [paperfoot/suno-cli releases](https://github.com/paperfoot/suno-cli/releases) or `cargo install suno`
2. `suno auth --login`
3. `suno doctor`
4. Point `SUNO_CLI_PATH` if not on PATH

## Risk register

| Risk | Mitigation |
|------|------------|
| Schema drift on v2-web | Track paperfoot releases; surface `schema_drift` errors |
| Captcha | MCP returns actionable message; user runs UI or `--token` |
| ToS | `docs/UNOFFICIAL.md` |
| Studio 2.0 | Out of scope until official API or CLI support |

## References

- Upstream CLI: https://github.com/paperfoot/suno-cli
- API notes: upstream `API_INTELLIGENCE.md`
- Fleet ports: mcp-central-docs `WEBAPP_PORTS.md` (10882/10883)
