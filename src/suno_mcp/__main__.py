"""Enable ``python -m suno_mcp``.

The fleet launcher runs ``python -m suno_mcp``. Without this file Python refuses with
"'suno_mcp' is a package and cannot be directly executed", and since the backend starts
in a hidden window that failure was silent -- the dashboard loaded and every API call
returned 404. Delegates to the entrypoint declared in pyproject.toml.
"""

from __future__ import annotations

import inspect
import sys

from suno_mcp.server import main


def _run() -> int:
    outcome = main()
    if inspect.iscoroutine(outcome):
        import asyncio

        outcome = asyncio.run(outcome)
    return 0 if outcome is None else outcome


if __name__ == "__main__":
    sys.exit(_run())
