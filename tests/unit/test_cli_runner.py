"""Tests for SunoCliBackend subprocess wrapper."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from suno_mcp.backends.cli_runner import SunoCliBackend
from suno_mcp.backends.config import SunoBackendConfig
from suno_mcp.tools.shared.exceptions import AuthenticationError, SunoError


@pytest.fixture
def backend(tmp_path) -> SunoCliBackend:
    config = SunoBackendConfig(
        backend="cli",
        cli_path="suno",
        cli_min_version="0.9.0",
        download_dir=tmp_path / "downloads",
        recon_enabled=False,
    )
    return SunoCliBackend(config)


@pytest.mark.asyncio
async def test_run_success_parses_json(backend: SunoCliBackend) -> None:
    payload = {"status": "ok", "data": {"credits": 100}}

    async def fake_exec(*cmd, stdout=None, stderr=None):
        proc = AsyncMock()
        proc.communicate = AsyncMock(return_value=(json.dumps(payload).encode(), b""))
        proc.returncode = 0
        return proc

    with patch("shutil.which", return_value="suno"), patch(
        "asyncio.create_subprocess_exec", side_effect=fake_exec
    ):
        result = await backend.run(["credits"], timeout_seconds=5)

    assert result.ok
    assert result.data == payload


@pytest.mark.asyncio
async def test_run_auth_error(backend: SunoCliBackend) -> None:
    err = {
        "status": "error",
        "error": {
            "code": "auth_expired",
            "message": "JWT expired",
            "suggestion": "Run suno auth --login",
        },
    }

    async def fake_exec(*cmd, stdout=None, stderr=None):
        proc = AsyncMock()
        proc.communicate = AsyncMock(return_value=(json.dumps(err).encode(), b"fail"))
        proc.returncode = 2
        return proc

    with patch("shutil.which", return_value="suno"), patch(
        "asyncio.create_subprocess_exec", side_effect=fake_exec
    ):
        with pytest.raises(AuthenticationError):
            await backend.run(["generate", "--title", "t", "--tags", "pop"])


@pytest.mark.asyncio
async def test_cli_missing_raises(backend: SunoCliBackend) -> None:
    with patch("shutil.which", return_value=None):
        with pytest.raises(SunoError) as exc:
            await backend.run(["doctor"])
    assert exc.value.code == "CLI_MISSING"
