"""Registration module for LangSmith MCP tools."""

from typing import Any, Dict, List, Optional

from fastmcp.server import Context

from langsmith_mcp_server.common.helpers import get_client_from_context
from langsmith_mcp_server.services.tools.datasets import (
    list_datasets_tool,
    list_examples_tool,
    read_dataset_tool,
    read_example_tool,
)
from langsmith_mcp_server.services.tools.prompts import (
    get_prompt_tool,
    list_prompts_tool,
)
from langsmith_mcp_server.services.tools.traces import (
    fetch_trace_tool,
    get_project_runs_stats_tool,
    get_thread_history_tool,
)


def register_tools(mcp, langsmith_client):
    """
    Register all LangSmith tool-related functionality with the MCP server.
    This function configures and registers various tools for interacting with LangSmith,
    including prompt management, conversation history, traces, and analytics.

    Args:
        mcp: The MCP server instance to register tools with
        langsmith_client: The LangSmith client instance for API access (ignored, uses request API key)
    """

    @mcp.tool()
    def list_prompts(is_public: str = "false", limit: int = 20, ctx: Context = None) -> Dict[str, Any]:
        """
        Fetch prompts from LangSmith with optional filtering.

        Args:
            is_public (str): Filter by prompt visibility - "true" for public prompts,
                            "false" for private prompts (default: "false")
            limit (int): Maximum number of prompts to return (default: 20)
            ctx: FastMCP context (automatically provided)

        Returns:
            Dict[str, Any]: Dictionary containing the prompts and metadata
        """
        try:
            client = get_client_from_context(ctx)
            is_public_bool = is_public.lower() == "true"
            return list_prompts_tool(client, is_public_bool, limit)
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def get_prompt_by_name(prompt_name: str, ctx: Context = None) -> Dict[str, Any]:
        """
        Get a specific prompt by its exact name.

        Args:
            prompt_name (str): The exact name of the prompt to retrieve
            ctx: FastMCP context (automatically provided)

        Returns:
            Dict[str, Any]: Dictionary containing the prompt details and template,
                          or an error message if the prompt cannot be found
        """
        try:
            client = get_client_from_context(ctx)
            return get_prompt_tool(client, prompt_name=prompt_name)
        except Exception as e:
            return {"error": str(e)}

    # Register conversation tools
    @mcp.tool()
    def get_thread_history(thread_id: str, project_name: str, ctx: Context = None) -> Dict[str, Any]:
        """
        Retrieve the message history for a specific conversation thread.

        Args:
            thread_id (str): The unique ID of the thread to fetch history for
            project_name (str): The name of the project containing the thread
                               (format: "owner/project" or just "project")
            ctx: FastMCP context (automatically provided)

        Returns:
            Dict[str, Any]: Dictionary containing the thread history,
                                or an error message if the thread cannot be found
        """
        try:
            client = get_client_from_context(ctx)
            return get_thread_history_tool(client, thread_id, project_name)
        except Exception as e:
            return {"error": str(e)}

    # Register analytics tools
    @mcp.tool()
    def get_project_runs_stats(project_name: str = None, trace_id: str = None, ctx: Context = None) -> Dict[str, Any]:
        """
        Get statistics about runs in a LangSmith project.

        Args:
            project_name (str): The name of the project to analyze
                              (format: "owner/project" or just "project")
            trace_id (str): The specific ID of the trace to fetch (preferred parameter)
            ctx: FastMCP context (automatically provided)

        Returns:
            Dict[str, Any]: Dictionary containing the requested project run statistics
                          or an error message if statistics cannot be retrieved
        """
        try:
            client = get_client_from_context(ctx)
            return get_project_runs_stats_tool(client, project_name, trace_id)
        except Exception as e:
            return {"error": str(e)}

    # Register trace tools
    @mcp.tool()
    def fetch_trace(project_name: str = None, trace_id: str = None, ctx: Context = None) -> Dict[str, Any]:
        """
        Fetch trace content for debugging and analyzing LangSmith runs.

        Note: Only one parameter (project_name or trace_id) is required.
        If both are provided, trace_id is preferred.
        String "null" inputs are handled as None values.

        Args:
            project_name (str, optional): The name of the project to fetch the latest trace from
            trace_id (str, optional): The specific ID of the trace to fetch (preferred parameter)
            ctx: FastMCP context (automatically provided)

        Returns:
            Dict[str, Any]: Dictionary containing the trace data and metadata,
                          or an error message if the trace cannot be found
        """
        try:
            client = get_client_from_context(ctx)
            return fetch_trace_tool(client, project_name, trace_id)
        except Exception as e:
            return {"error": str(e)}

    # Register dataset tools
    @mcp.tool()
    def list_datasets(
        dataset_ids: Optional[List[str]] = None,
        data_type: Optional[str] = None,
        dataset_name: Optional[str] = None,
        dataset_name_contains: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        Fetch LangSmith datasets.

        Note: If no arguments are provided, all datasets will be returned.

        Args:
            dataset_ids (Optional[List[str]]): List of dataset IDs to filter by
            data_type (Optional[str]): Filter by dataset data type (e.g., 'chat', 'kv')
            dataset_name (Optional[str]): Filter by exact dataset name
            dataset_name_contains (Optional[str]): Filter by substring in dataset name
            metadata (Optional[Dict[str, Any]]): Filter by metadata dict
            limit (int): Max number of datasets to return (default: 20)
            ctx: FastMCP context (automatically provided)

        Returns:
            Dict[str, Any]: Dictionary containing the datasets and metadata,
                            or an error message if the datasets cannot be retrieved
        """
        try:
            client = get_client_from_context(ctx)
            return list_datasets_tool(
                client,
                dataset_ids=dataset_ids,
                data_type=data_type,
                dataset_name=dataset_name,
                dataset_name_contains=dataset_name_contains,
                metadata=metadata,
                limit=limit,
            )
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def list_examples(
        dataset_id: Optional[str] = None,
        dataset_name: Optional[str] = None,
        example_ids: Optional[List[str]] = None,
        filter: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        splits: Optional[List[str]] = None,
        inline_s3_urls: Optional[bool] = None,
        include_attachments: Optional[bool] = None,
        as_of: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        Fetch examples from a LangSmith dataset with advanced filtering options.

        Note: Either dataset_id, dataset_name, or example_ids must be provided.
        If multiple are provided, they are used in order of precedence: example_ids, dataset_id, dataset_name.

        Args:
            dataset_id (Optional[str]): Dataset ID to retrieve examples from
            dataset_name (Optional[str]): Dataset name to retrieve examples from
            example_ids (Optional[List[str]]): List of specific example IDs to retrieve
            limit (Optional[int]): Maximum number of examples to return
            offset (Optional[int]): Number of examples to skip before starting to return results
            filter (Optional[str]): Filter string using LangSmith query syntax (e.g., 'has(metadata, {"key": "value"})')
            metadata (Optional[Dict[str, Any]]): Dictionary of metadata to filter by
            splits (Optional[List[str]]): List of dataset splits to include examples from
            inline_s3_urls (Optional[bool]): Whether to inline S3 URLs (default: SDK default if not specified)
            include_attachments (Optional[bool]): Whether to include attachments in response (default: SDK default if not specified)
            as_of (Optional[str]): Dataset version tag OR ISO timestamp to retrieve examples as of that version/time
            ctx: FastMCP context (automatically provided)

        Returns:
            Dict[str, Any]: Dictionary containing the examples and metadata,
                            or an error message if the examples cannot be retrieved
        """
        try:
            client = get_client_from_context(ctx)
            return list_examples_tool(
                client,
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                example_ids=example_ids,
                filter=filter,
                metadata=metadata,
                splits=splits,
                inline_s3_urls=inline_s3_urls,
                include_attachments=include_attachments,
                as_of=as_of,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def read_dataset(
        dataset_id: Optional[str] = None,
        dataset_name: Optional[str] = None,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        Read a specific dataset from LangSmith.

        Note: Either dataset_id or dataset_name must be provided to identify the dataset.
        If both are provided, dataset_id takes precedence.

        Args:
            dataset_id (Optional[str]): Dataset ID to retrieve
            dataset_name (Optional[str]): Dataset name to retrieve
            ctx: FastMCP context (automatically provided)

        Returns:
            Dict[str, Any]: Dictionary containing the dataset details,
                            or an error message if the dataset cannot be retrieved
        """
        try:
            client = get_client_from_context(ctx)
            return read_dataset_tool(
                client,
                dataset_id=dataset_id,
                dataset_name=dataset_name,
            )
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def read_example(
        example_id: str,
        as_of: Optional[str] = None,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        Read a specific example from LangSmith.

        Args:
            example_id (str): Example ID to retrieve
            as_of (Optional[str]): Dataset version tag OR ISO timestamp to retrieve the example as of that version/time
            ctx: FastMCP context (automatically provided)

        Returns:
            Dict[str, Any]: Dictionary containing the example details,
                            or an error message if the example cannot be retrieved
        """
        try:
            client = get_client_from_context(ctx)
            return read_example_tool(
                client,
                example_id=example_id,
                as_of=as_of,
            )
        except Exception as e:
            return {"error": str(e)}
