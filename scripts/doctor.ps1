# Suno MCP + paperfoot suno-cli health check
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "=== suno-mcp doctor ===" -ForegroundColor Cyan

$cli = $env:SUNO_CLI_PATH
if (-not $cli) {
    $cli = "suno"
}

$cliCmd = Get-Command $cli -ErrorAction SilentlyContinue
if (-not $cliCmd) {
    Write-Host "FAIL: Suno CLI not found ($cli). Install from https://github.com/paperfoot/suno-cli/releases" -ForegroundColor Red
    exit 2
}

Write-Host "CLI: $($cliCmd.Source)"
& $cli doctor
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== MCP package import ===" -ForegroundColor Cyan
uv run python -c "import suno_mcp.server as s; print('version', s.SERVER_VERSION)"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "OK" -ForegroundColor Green
