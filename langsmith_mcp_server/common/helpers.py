"""Helper functions for the LangSmith MCP server."""

import os
import re
from datetime import datetime
from typing import Optional, Union

from fastmcp.server import Context
from langsmith import Client


def get_langsmith_client_from_api_key(api_key: str, workspace_id: Optional[str] = None, endpoint: Optional[str] = None) -> Client:
    """
    Create a LangSmith client from an API key and optional configuration.
    
    Args:
        api_key: The LangSmith API key (required)
        workspace_id: Optional workspace ID for API keys scoped to multiple workspaces
        endpoint: Optional custom endpoint URL (e.g., for self-hosted installations or EU region)
        
    Returns:
        LangSmith Client instance
    """
    # Set environment variables for LangSmith client (some SDK operations read from env)
    os.environ["LANGSMITH_API_KEY"] = api_key
    if workspace_id:
        os.environ["LANGSMITH_WORKSPACE_ID"] = workspace_id
    if endpoint:
        os.environ["LANGSMITH_ENDPOINT"] = endpoint
    
    # Initialize the LangSmith client with parameters
    client_kwargs = {"api_key": api_key}
    if workspace_id:
        client_kwargs["workspace_id"] = workspace_id
    if endpoint:
        client_kwargs["api_url"] = endpoint
    
    return Client(**client_kwargs)


def get_client_from_context(ctx: Context) -> Client:
    """
    Get LangSmith client from API key and optional config using FastMCP context.
    
    Supports both HTTP and STDIO transports:
    - HTTP: Config extracted from headers (LANGSMITH-API-KEY, etc.) and stored in session
    - STDIO: Config read from environment variables (LANGSMITH_API_KEY, etc.)
    
    On first HTTP request, config is extracted from headers and stored in session.
    On subsequent HTTP requests, config is retrieved from session state.
    For STDIO, config is always read from environment variables.
    
    Args:
        ctx: FastMCP context (automatically provided to tools)
        
    Returns:
        LangSmith Client instance
        
    Raises:
        ValueError: If API key is not found in headers (HTTP) or environment (STDIO)
    """
    # Try to get config from session state (set on first HTTP request)
    api_key = ctx.get_state("api_key")
    workspace_id = ctx.get_state("workspace_id") or None
    endpoint = ctx.get_state("endpoint") or None
    
    # If not in session, try to get from request headers (HTTP transport)
    if not api_key:
        request = ctx.get_http_request()
        if request:
            # HTTP transport: get from headers
            api_key = request.headers.get("LANGSMITH-API-KEY")
            workspace_id = request.headers.get("LANGSMITH-WORKSPACE-ID") or None
            endpoint = request.headers.get("LANGSMITH-ENDPOINT") or None
            
            # Store in session for future requests
            if api_key:
                ctx.set_state("api_key", api_key)
                if workspace_id:
                    ctx.set_state("workspace_id", workspace_id)
                if endpoint:
                    ctx.set_state("endpoint", endpoint)
        else:
            # STDIO transport: get from environment variables
            api_key = os.environ.get("LANGSMITH_API_KEY")
            workspace_id = os.environ.get("LANGSMITH_WORKSPACE_ID") or None
            endpoint = os.environ.get("LANGSMITH_ENDPOINT") or None
    
    if not api_key:
        raise ValueError(
            "API key not found. For HTTP transport, provide LANGSMITH-API-KEY header. "
            "For STDIO transport, set LANGSMITH_API_KEY environment variable."
        )
    
    return get_langsmith_client_from_api_key(api_key, workspace_id=workspace_id, endpoint=endpoint)


def get_langgraph_app_host_name(run_stats: dict) -> Optional[str]:
    """
    Get the langgraph app host name from the run stats

    Args:
        run_stats (dict): The run stats

    Returns:
        str | None: The langgraph app host name
    """
    if run_stats and run_stats.get("run_facets"):
        for run_facet in run_stats["run_facets"]:
            try:
                for rfk in run_facet.keys():
                    langgraph_host = re.search(r"http[s]?:\/\/(?P<langgraph_host>[^\/]+)", rfk)
                    if langgraph_host:
                        return langgraph_host.group("langgraph_host")
            except re.error:
                continue
    return None


def _parse_as_of_parameter(as_of: str) -> Union[datetime, str]:
    """
    Parse the as_of parameter, converting ISO timestamps to datetime objects
    while leaving version tags as strings.

    Args:
        as_of: Dataset version tag OR ISO timestamp string

    Returns:
        datetime object if as_of is a valid ISO timestamp, otherwise the original string
    """
    try:
        # Try to parse as ISO format datetime
        return datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        # If parsing fails, assume it's a version tag and return as string
        return as_of
