"""Async subprocess wrapper for paperfoot/suno-cli."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
from dataclasses import dataclass
from typing import Any

from ..tools.shared.exceptions import AuthenticationError, GenerationError, SunoError
from .config import SunoBackendConfig, load_config

logger = logging.getLogger(__name__)

_VERSION_RE = re.compile(r"v?(\d+\.\d+\.\d+)")


@dataclass
class CliRunResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str
    data: dict[str, Any] | list[Any] | None

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class SunoCliBackend:
    """Run `suno` CLI commands with JSON parsing and semantic errors."""

    def __init__(self, config: SunoBackendConfig | None = None) -> None:
        self.config = config or load_config()

    def _resolve_cli(self) -> str:
        path = self.config.cli_path
        if shutil.which(path):
            return path
        raise SunoError(
            f"Suno CLI not found at '{path}'. Install paperfoot/suno-cli "
            "(GitHub Releases or cargo install suno) and set SUNO_CLI_PATH.",
            code="CLI_MISSING",
        )

    async def run(
        self,
        args: list[str],
        *,
        timeout_seconds: float = 120.0,
        json_output: bool = True,
    ) -> CliRunResult:
        cli = self._resolve_cli()
        argv = [cli, *args]
        if json_output and "--json" not in args:
            argv.append("--json")

        logger.info("Running suno CLI: %s", " ".join(argv))

        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds,
            )
        except TimeoutError as exc:
            proc.kill()
            await proc.wait()
            raise SunoError(
                f"suno CLI timed out after {timeout_seconds}s: {' '.join(args)}",
                code="CLI_TIMEOUT",
            ) from exc

        stdout = stdout_b.decode("utf-8", errors="replace").strip()
        stderr = stderr_b.decode("utf-8", errors="replace").strip()
        returncode = proc.returncode if proc.returncode is not None else 1
        data = self._parse_json(stdout) if stdout else None

        result = CliRunResult(
            argv=argv,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            data=data,
        )
        if not result.ok:
            self._raise_for_result(result)
        return result

    def _parse_json(self, stdout: str) -> dict[str, Any] | list[Any] | None:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, (dict, list)):
            return parsed
        return None

    def _raise_for_result(self, result: CliRunResult) -> None:
        code = "CLI_ERROR"
        message = result.stderr or result.stdout or "suno CLI failed"
        suggestion = ""

        if isinstance(result.data, dict):
            err = result.data.get("error")
            if isinstance(err, dict):
                code = str(err.get("code", code))
                message = str(err.get("message", message))
                suggestion = str(err.get("suggestion", ""))

        if result.returncode == 2 or code in (
            "auth_expired",
            "auth_missing",
            "configuration",
        ):
            hint = suggestion or "Run `suno auth --login` or `suno auth --refresh`, then `suno doctor`."
            raise AuthenticationError(f"{message}. {hint}", code=code)

        if result.returncode == 3:
            raise SunoError(message, code=code or "BAD_INPUT")

        if code in ("schema_drift", "captcha_required"):
            raise GenerationError(message, code=code)

        if result.returncode == 1:
            raise GenerationError(message, code=code)

        raise SunoError(message, code=code)

    async def doctor(self) -> CliRunResult:
        return await self.run(["doctor"], timeout_seconds=180.0)

    async def credits(self) -> CliRunResult:
        return await self.run(["credits"], timeout_seconds=60.0)

    async def generate(
        self,
        *,
        title: str,
        tags: str,
        lyrics: str | None = None,
        lyrics_file: str | None = None,
        instrumental: bool = False,
        model: str | None = None,
        download_dir: str | None = None,
        wait: bool = True,
    ) -> CliRunResult:
        args: list[str] = ["generate", "--title", title, "--tags", tags]
        if lyrics_file:
            args.extend(["--lyrics-file", lyrics_file])
        elif lyrics:
            args.extend(["--lyrics", lyrics])
        if instrumental:
            args.append("--instrumental")
        if model:
            args.extend(["--model", model])
        if wait:
            args.append("--wait")
        dest = download_dir or str(self.config.download_dir)
        self.config.download_dir.mkdir(parents=True, exist_ok=True)
        args.extend(["--download", dest])
        return await self.run(args, timeout_seconds=900.0)

    async def describe(
        self,
        *,
        prompt: str,
        title: str | None = None,
        wait: bool = True,
    ) -> CliRunResult:
        args: list[str] = ["describe", "--prompt", prompt]
        if title:
            args.extend(["--title", title])
        if wait:
            args.append("--wait")
        return await self.run(args, timeout_seconds=900.0)

    async def write_scaffold(
        self,
        *,
        genre: str,
        theme: str,
        vocal: str | None = None,
        out_path: str | None = None,
    ) -> CliRunResult:
        args: list[str] = ["write", "--genre", genre, "--theme", theme]
        if vocal:
            args.extend(["--vocal", vocal])
        if out_path:
            args.extend(["--out", out_path])
        return await self.run(args, timeout_seconds=120.0)

    async def status_snapshot(self) -> dict[str, Any]:
        """Lightweight status for HTTP dashboard (credits probe, no full doctor)."""
        installed = shutil.which(self.config.cli_path) is not None
        version = await self.cli_version() if installed else None
        ready = False
        credits_data: dict[str, Any] | None = None
        error_message = ""
        if installed:
            try:
                result = await self.run(["credits"], timeout_seconds=25.0)
                ready = True
                if isinstance(result.data, dict):
                    credits_data = result.data
            except SunoError as exc:
                error_message = str(exc)
        return {
            "cli_installed": installed,
            "cli_version": version,
            "cli_ready": ready,
            "cli_credits": credits_data,
            "cli_error": error_message or None,
            "cli_path": self.config.cli_path,
            "cli_min_version": self.config.cli_min_version,
        }

    async def cli_version(self) -> str | None:
        cli = self._resolve_cli()
        proc = await asyncio.create_subprocess_exec(
            cli,
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, stderr_b = await proc.communicate()
        text = (stdout_b or stderr_b).decode("utf-8", errors="replace").strip()
        match = _VERSION_RE.search(text)
        return match.group(1) if match else None

    def format_result_for_agent(self, result: CliRunResult) -> str:
        if isinstance(result.data, dict):
            return json.dumps(result.data, indent=2)
        if isinstance(result.data, list):
            return json.dumps(result.data, indent=2)
        if result.stdout:
            return result.stdout
        return json.dumps({"status": "ok", "stderr": result.stderr}, indent=2)
