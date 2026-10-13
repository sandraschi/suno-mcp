"""Environment configuration for suno-mcp backends."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _backend_mode() -> str:
    raw = os.getenv("SUNO_BACKEND", "cli").strip().lower()
    if raw in ("cli", "playwright"):
        return raw
    return "cli"


@dataclass(frozen=True)
class SunoBackendConfig:
    backend: str
    cli_path: str
    cli_min_version: str
    download_dir: Path
    recon_enabled: bool

    @classmethod
    def from_env(cls) -> SunoBackendConfig:
        download = Path(os.getenv("SUNO_DOWNLOAD_DIR", "downloads"))
        recon = os.getenv("SUNO_ENABLE_RECON", "").lower() in ("1", "true", "yes")
        return cls(
            backend=_backend_mode(),
            cli_path=os.getenv("SUNO_CLI_PATH", "suno"),
            cli_min_version=os.getenv("SUNO_CLI_MIN_VERSION", "0.9.0"),
            download_dir=download,
            recon_enabled=recon,
        )


def load_config() -> SunoBackendConfig:
    return SunoBackendConfig.from_env()
