"""
Vercel serverless entry point for the LangSmith MCP Server.

Exposes the ASGI app so Vercel's Python runtime can serve MCP over HTTP.
Set LANGSMITH_API_KEY in the project's Environment Variables (or send
LANGSMITH-API-KEY header per request).
"""
from langsmith_mcp_server.server import app

__all__ = ["app"]
