"""Suno MCP Server - Automated Suno AI Music Generation.

This package provides an MCP (Model Context Protocol) server that automates
Suno AI music generation and includes reconnaissance tools for Studio 
DOM analysis to enable automation development.

Features:
- Basic music generation via Playwright browser automation
- Studio reconnaissance for DOM structure discovery
- Cookie-based session persistence for auth
- Interactive element mapping for automation selectors
"""

__version__ = "1.2.0"
__author__ = "Sandra Schipal"

from .server import fastapi_app, mcp_app

__all__ = ["fastapi_app", "mcp_app"]
