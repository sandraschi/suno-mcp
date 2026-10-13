"""MCP-facing methods for the paperfoot suno CLI backend."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from ...backends.cli_runner import SunoCliBackend
from ...backends.config import load_config
from ..shared.exceptions import SunoError


class CliSunoTools:
    """High-level tool handlers backed by SunoCliBackend."""

    def __init__(self, backend: SunoCliBackend | None = None) -> None:
        self.backend = backend or SunoCliBackend(load_config())

    async def auth_status(self) -> str:
        doctor = await self.backend.doctor()
        credits = await self.backend.credits()
        version = await self.backend.cli_version()
        payload = {
            "cli_version": version,
            "min_recommended": self.backend.config.cli_min_version,
            "doctor": doctor.data,
            "credits": credits.data,
        }
        return json.dumps(payload, indent=2)

    async def generate(
        self,
        title: str,
        tags: str,
        lyrics: str | None = None,
        instrumental: bool = False,
        model: str | None = None,
        download_dir: str | None = None,
    ) -> str:
        lyrics_file: str | None = None
        temp_path: Path | None = None
        try:
            if lyrics and len(lyrics) > 500:
                fd, tmp_name = tempfile.mkstemp(suffix=".txt", prefix="suno-lyrics-")
                os.close(fd)
                temp_path = Path(tmp_name)
                temp_path.write_text(lyrics, encoding="utf-8")
                lyrics_file = str(temp_path)
                lyrics = None
            result = await self.backend.generate(
                title=title,
                tags=tags,
                lyrics=lyrics,
                lyrics_file=lyrics_file,
                instrumental=instrumental,
                model=model,
                download_dir=download_dir,
            )
            return self.backend.format_result_for_agent(result)
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)

    async def describe(self, prompt: str, title: str | None = None) -> str:
        result = await self.backend.describe(prompt=prompt, title=title)
        return self.backend.format_result_for_agent(result)

    async def write_scaffold(
        self,
        genre: str,
        theme: str,
        vocal: str | None = None,
    ) -> str:
        out_dir = self.backend.config.download_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"suno-write-{genre.replace(' ', '-')}.txt"
        result = await self.backend.write_scaffold(
            genre=genre,
            theme=theme,
            vocal=vocal,
            out_path=str(out_path),
        )
        return self.backend.format_result_for_agent(result)


def ensure_cli_backend() -> None:
    if load_config().backend != "cli":
        raise SunoError(
            "CLI tools require SUNO_BACKEND=cli (default). Set SUNO_BACKEND=playwright for legacy UI tools.",
            code="WRONG_BACKEND",
        )
