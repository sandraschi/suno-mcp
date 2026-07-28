"""Custom exceptions for Suno MCP tools."""


class SunoError(Exception):
    """Custom exception for Suno-related errors."""

    def __init__(self, message: str, code: str = "SUNO_ERROR") -> None:
        super().__init__(message)
        self.code = code


class BrowserError(SunoError):
    """Browser-related errors."""

    pass


class AuthenticationError(SunoError):
    """Authentication-related errors."""

    pass


class GenerationError(SunoError):
    """Music generation-related errors."""

    pass


class DownloadError(SunoError):
    """Download-related errors."""

    pass


class StudioError(SunoError):
    """Studio/DAW-related errors."""

    pass
