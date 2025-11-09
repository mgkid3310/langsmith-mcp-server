"""Registration module for LangSmith MCP tools."""

import json
from typing import Any, Dict, List, Optional, Union

from fastmcp import FastMCP
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
    fetch_runs_tool,
    fetch_trace_tool,
    get_project_runs_stats_tool,
    get_thread_history_tool,
    list_projects_tool,
)


def register_tools(mcp: FastMCP) -> None:
    """
    Register all LangSmith tool-related functionality with the MCP server.
    This function configures and registers various tools for interacting with LangSmith,
    including prompt management, conversation history, traces, and analytics.

    Args:
        mcp: The MCP server instance to register tools with
    """

    @mcp.tool()
    def list_prompts(is_public: str = "false", limit: int = 20, ctx: Context = None) -> Dict[str, Any]:
        """
        Fetch prompts from LangSmith with optional filtering.

        Args:
            is_public (str): Filter by prompt visibility - "true" for public prompts,
                            "false" for private prompts (default: "false")
            limit (int): Maximum number of prompts to return (default: 20)

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

    @mcp.tool()
    def push_prompt(ctx: Context = None) -> None:
        """
        Documentation tool for understanding how to create and push prompts to LangSmith.

        This tool provides comprehensive documentation on creating ChatPromptTemplate and
        StructuredPrompt objects and pushing them to LangSmith using the LangSmith Client.

        ---
        🧩 PURPOSE
        ----------
        This is a **documentation-only tool** that explains how to:
        - Create prompts using LangChain's prompt templates
        - Push prompts to LangSmith for version control and management
        - Handle prompt creation vs. version updates

        ---
        📦 REQUIRED DEPENDENCIES
        ------------------------
        To use the functionality described in this documentation, you need:
        - `langsmith` - The LangSmith Python client
        - `langchain-core` - Core LangChain functionality for prompt templates
        - `langchain` (optional) - Required only if using `from langchain.messages` imports

        Install with:
        ```bash
        pip install langsmith langchain-core
        # Optional, for message classes:
        pip install langchain
        ```

        ---
        🔧 HOW TO PUSH PROMPTS
        -----------------------
        Use the LangSmith Client's `push_prompt()` method:

        ```python
        from langsmith import Client

        client = Client()

        url = client.push_prompt(
            prompt_identifier="my-prompt-name",
            object=prompt,  # Your prompt object
            description="Optional description",
            tags=["tag1", "tag2"],  # Optional tags
            is_public=False,  # Optional visibility (True/False)
        )
        ```

        **Behavior:**
        - If the prompt name **doesn't exist**: Creates a new prompt in LangSmith
        - If the prompt name **exists** and it's a **new version**: Creates a new commit/version
        - If the prompt name **exists** and it's the **same version**: No new commit is created

        ---
        📝 CREATING CHATPROMPTTEMPLATE PROMPTS
        --------------------------------------

        1️⃣ **Basic ChatPromptTemplate**
        ```python
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant. Your name is {assistant_name}."),
            ("human", "{user_input}"),
        ])

        client.push_prompt("my-chat-prompt", object=prompt)
        ```

        2️⃣ **Using Message Classes**
        ```python
        from langchain_core.prompts import ChatPromptTemplate
        from langchain.messages import SystemMessage, HumanMessage, AIMessage

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are a coding assistant."),
            HumanMessage(content="Write a Python function to {task}"),
            AIMessage(content="I'll help you write that function."),
            ("human", "Make it {style}"),
        ])

        client.push_prompt("my-message-classes-prompt", object=prompt)
        ```

        3️⃣ **With MessagesPlaceholder for Conversation History**
        ```python
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            MessagesPlaceholder(variable_name="conversation", optional=True),
            ("human", "{user_input}"),
        ])

        client.push_prompt("my-conversation-prompt", object=prompt)
        ```

        4️⃣ **Complex Prompt with Multiple Placeholders**
        ```python
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain.messages import HumanMessage

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are {assistant_name}, a {role} assistant."),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "Current question: {question}"),
            ("ai", "Let me think about that..."),
            MessagesPlaceholder(variable_name="tool_results", optional=True),
            HumanMessage(content="Based on the above, what's your final answer?"),
        ])

        client.push_prompt("my-complex-prompt", object=prompt)
        ```

        ---
        🎯 CREATING STRUCTUREDPROMPT PROMPTS
        ------------------------------------

        StructuredPrompt allows you to define output schemas for structured outputs.

        1️⃣ **With Dictionary Schema (with title and description)**
        ```python
        from langchain_core.prompts.structured import StructuredPrompt

        schema = {
            "title": "SentimentAnalysis",
            "description": "Analyzes the sentiment of text with confidence and reasoning",
            "type": "object",
            "properties": {
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral"],
                    "description": "The sentiment of the text"
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence score between 0 and 1"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief reasoning for the sentiment"
                }
            },
            "required": ["sentiment", "confidence", "reasoning"],
            "strict": True
        }

        prompt = StructuredPrompt(
            [
                ("system", "You are a sentiment analysis expert."),
                ("human", "Analyze the sentiment of: {text}"),
            ],
            schema_=schema,
        )

        client.push_prompt("my-structured-prompt", object=prompt)
        ```

        2️⃣ **With Pydantic Model (Convert to Dict Schema)**
        ```python
        from langchain_core.prompts.structured import StructuredPrompt
        from pydantic import BaseModel, Field

        class UserInfo(BaseModel):
            '''User information extracted from text.'''
            name: str = Field(description="The user's name")
            age: int = Field(description="The user's age")
            email: str = Field(description="The user's email address")

        # Convert Pydantic model to dict schema
        schema_dict = UserInfo.model_json_schema()
        # Add title and description at top level if not present
        if "title" not in schema_dict:
            schema_dict["title"] = UserInfo.__name__
        if "description" not in schema_dict:
            schema_dict["description"] = UserInfo.__doc__ or f"Schema for {UserInfo.__name__}"

        prompt = StructuredPrompt(
            [
                ("system", "You are a helpful assistant that extracts user information."),
                ("human", "Extract information from: {text}"),
            ],
            schema_=schema_dict,
        )

        client.push_prompt("my-pydantic-prompt", object=prompt)
        ```

        ---
        🧠 HELPER FUNCTION PATTERN
        ---------------------------
        You can create a reusable helper function:

        ```python
        def push_prompt_to_langsmith(
            prompt,
            prompt_identifier: str,
            description: str = None,
            tags: list = None,
            is_public: bool = None,
        ) -> str:
            '''
            Push a prompt to LangSmith with optional metadata.
            
            Args:
                prompt: The prompt object (ChatPromptTemplate, StructuredPrompt, etc.)
                prompt_identifier: The name/identifier for the prompt
                description: Optional description of the prompt
                tags: Optional list of tags
                is_public: Optional visibility setting (True/False)
            
            Returns:
                The URL of the pushed prompt
            '''
            kwargs = {"object": prompt}
            if description:
                kwargs["description"] = description
            if tags:
                kwargs["tags"] = tags
            if is_public is not None:
                kwargs["is_public"] = is_public
            
            url = client.push_prompt(prompt_identifier, **kwargs)
            return url
        ```

        ---
        📤 RETURNS
        ----------
        None
            This tool is documentation-only and returns None. The documentation is in the docstring.

        ---
        🧠 NOTES FOR AGENTS
        --------------------
        - This tool is **documentation-only** - it does not execute any code
        - Use this tool to understand how to create and push prompts programmatically
        - The `push_prompt()` method automatically handles versioning:
          - New prompt name → creates new prompt
          - Existing prompt name with changes → creates new version/commit
          - Existing prompt name with no changes → no new commit
        - Always ensure you have the required dependencies installed before using these patterns
        - Prompt identifiers should be unique and descriptive
        - Use tags and descriptions to organize and document your prompts

        ---
        🔐 ENVIRONMENT VARIABLES
        -------------------------
        Before using the LangSmith Client, make sure to set up your environment variables:

        **Required:**
        ```bash
        export LANGSMITH_API_KEY="lsv2_pt_..."
        ```

        **Optional:**
        ```bash
        # Only needed if using a custom endpoint (defaults to cloud if not set)
        export LANGSMITH_ENDPOINT="https://api.smith.langchain.com"

        # Only needed if you want to specify a workspace
        export LANGSMITH_WORKSPACE_ID="35e66a3b-2973-4830-83e1-352c43a660ed"
        ```

        You can also use a `.env` file with `python-dotenv`:
        ```python
        from dotenv import load_dotenv
        load_dotenv()  # Loads variables from .env file

        from langsmith import Client
        client = Client()  # Will automatically use environment variables
        ```
        """
        return None

    # Register conversation tools
    # @mcp.tool()
    # def get_thread_history(thread_id: str, project_name: str, ctx: Context = None) -> Dict[str, Any]:
    #     """
    #     Retrieve the message history for a specific conversation thread.

    #     Args:
    #         thread_id (str): The unique ID of the thread to fetch history for
    #         project_name (str): The name of the project containing the thread
    #                            (format: "owner/project" or just "project")

    #     Returns:
    #         Dict[str, Any]: Dictionary containing the thread history,
    #                             or an error message if the thread cannot be found
    #     """
    #     try:
    #         client = get_client_from_context(ctx)
    #         return get_thread_history_tool(client, thread_id, project_name)
    #     except Exception as e:
    #         return {"error": str(e)}

    # Register analytics tools
    # @mcp.tool()
    # def get_project_runs_stats(project_name: str = None, trace_id: str = None, ctx: Context = None) -> Dict[str, Any]:
    #     """
    #     Get statistics about runs in a LangSmith project.

    #     Args:
    #         project_name (str): The name of the project to analyze
    #                           (format: "owner/project" or just "project")
    #         trace_id (str): The specific ID of the trace to fetch (preferred parameter)

    #     Returns:
    #         Dict[str, Any]: Dictionary containing the requested project run statistics
    #                       or an error message if statistics cannot be retrieved
    #     """
    #     try:
    #         client = get_client_from_context(ctx)
    #         return get_project_runs_stats_tool(client, project_name, trace_id)
    #     except Exception as e:
    #         return {"error": str(e)}

    # # Register trace tools
    # @mcp.tool()
    # def fetch_trace(project_name: str = None, trace_id: str = None, ctx: Context = None) -> Dict[str, Any]:
    #     """
    #     Fetch trace content for debugging and analyzing LangSmith runs.

    #     Note: Only one parameter (project_name or trace_id) is required.
    #     If both are provided, trace_id is preferred.
    #     String "null" inputs are handled as None values.

    #     Args:
    #         project_name (str, optional): The name of the project to fetch the latest trace from
    #         trace_id (str, optional): The specific ID of the trace to fetch (preferred parameter)

    #     Returns:
    #         Dict[str, Any]: Dictionary containing the trace data and metadata,
    #                       or an error message if the trace cannot be found
    #     """
    #     try:
    #         client = get_client_from_context(ctx)
    #         return fetch_trace_tool(client, project_name, trace_id)
    #     except Exception as e:
    #         return {"error": str(e)}

    @mcp.tool()
    def fetch_runs(
        project_name: str,
        trace_id: str = None,
        run_type: str = None,
        error: str = None,
        is_root: str = None,
        filter: str = None,
        trace_filter: str = None,
        tree_filter: str = None,
        order_by: str = "-start_time",
        limit: int = 50,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        Fetch LangSmith runs (traces, tools, chains, etc.) from one or more projects
        using flexible filters, query language expressions, and trace-level constraints.

        ---
        🧩 PURPOSE
        ----------
        This is a **general-purpose LangSmith run fetcher** designed for analytics,
        trace export, and automated exploration.

        It wraps `client.list_runs()` with complete support for:
        - Multiple project names or IDs
        - The **Filter Query Language (FQL)** for precise queries
        - Hierarchical filtering across trace trees
        - Sorting and result limiting

        It returns **raw `dict` objects** suitable for further analysis or export.

        ---
        ⚙️ PARAMETERS
        -------------
        project_name : str
            The project name to fetch runs from. For multiple projects, use JSON array string (e.g., '["project1", "project2"]').

        trace_id : str, optional
            Return only runs that belong to a specific trace tree.
            It is a UUID string, e.g. "123e4567-e89b-12d3-a456-426614174000".

        run_type : str, optional
            Filter runs by type (e.g. "llm", "chain", "tool", "retriever").

        error : str, optional
            Filter by error status: "true" for errored runs, "false" for successful runs.

        is_root : str, optional
            Filter root traces: "true" for only top-level traces, "false" to exclude roots.
            If not provided, returns all runs.

        filter : str, optional
            A **Filter Query Language (FQL)** expression that filters runs by fields,
            metadata, tags, feedback, latency, or time.

            ─── Common field names ───
            - `id`, `name`, `run_type`
            - `start_time`, `end_time`
            - `latency`
            - `total_tokens`
            - `error`
            - `tags`
            - `feedback_key`, `feedback_score`
            - `metadata_key`, `metadata_value`
            - `execution_order`

            ─── Supported comparators ───
            - `eq`, `neq` → equal / not equal
            - `gt`, `gte`, `lt`, `lte` → numeric or time comparisons
            - `has` → tag or metadata contains value
            - `search` → substring or full-text match
            - `and`, `or`, `not` → logical operators

            ─── Examples ───
            ```python
            'gt(latency, "5s")'                                # took longer than 5 seconds
            'neq(error, null)'                                  # errored runs
            'has(tags, "beta")'                                 # runs tagged "beta"
            'and(eq(name,"ChatOpenAI"), eq(run_type,"llm"))'    # named & typed runs
            'search("image classification")'                    # full-text search
            ```

        trace_filter : str, optional
            Filter applied **to the root run** in each trace tree.
            Lets you select child runs based on root attributes or feedback.

            Example:
            ```python
            'and(eq(feedback_key,"user_score"), eq(feedback_score,1))'
            ```
            → return runs whose root trace has a user_score of 1.

        tree_filter : str, optional
            Filter applied **to any run** in the trace tree (including siblings or children).
            Example:
            ```python
            'eq(name,"ExpandQuery")'
            ```
            → return runs if *any* run in their trace had that name.

        order_by : str, default "-start_time"
            Sort field; prefix with "-" for descending order.

        limit : int, default 50
            Maximum number of runs to return.

        ---
        📤 RETURNS
        ----------
        List[dict]
            A list of LangSmith `dict` objects that satisfy the query.

        ---
        🧪 EXAMPLES
        ------------
        1️⃣ **Get latest 10 root runs**
        ```python
        runs = fetch_runs("alpha-project", is_root="true", limit=10)
        ```

        2️⃣ **Get all tool runs that errored**
        ```python
        runs = fetch_runs("alpha-project", run_type="tool", error="true")
        ```

        3️⃣ **Get all runs that took >5s and have tag "experimental"**
        ```python
        runs = fetch_runs("alpha-project", filter='and(gt(latency,"5s"), has(tags,"experimental"))')
        ```

        4️⃣ **Get all runs in a specific conversation thread**
        ```python
        thread_id = "abc-123"
        fql = f'and(in(metadata_key, ["session_id","conversation_id","thread_id"]), eq(metadata_value, "{thread_id}"))'
        runs = fetch_runs("alpha-project", is_root="true", filter=fql)
        ```

        5️⃣ **List all runs called "extractor" whose root trace has feedback user_score=1**
        ```python
        runs = fetch_runs(
            "alpha-project",
            filter='eq(name,"extractor")',
            trace_filter='and(eq(feedback_key,"user_score"), eq(feedback_score,1))'
        )
        ```

        6️⃣ **List all runs that started after a timestamp and either errored or got low feedback**
        ```python
        fql = 'and(gt(start_time,"2023-07-15T12:34:56Z"), or(neq(error,null), and(eq(feedback_key,"Correctness"), eq(feedback_score,0.0))))'
        runs = fetch_runs("alpha-project", filter=fql)
        ```

        ---
        🧠 NOTES FOR AGENTS
        --------------------
        - Use this to **query LangSmith data sources dynamically**.
        - Compose FQL strings programmatically based on your intent.
        - Combine `filter`, `trace_filter`, and `tree_filter` for hierarchical logic.
        - Always verify that `project_name` matches an existing LangSmith project.
        - Returned `dict` objects have fields like:
        - `id`, `name`, `run_type`, `inputs`, `outputs`, `error`, `start_time`, `end_time`, `latency`, `metadata`, `feedback`, etc.
        - If the trace is big, save it to a file (if you have this ability) and analyze it locally.
        """
        try:
            client = get_client_from_context(ctx)
            
            # Parse project_name - can be a single string or JSON array
            parsed_project_name = project_name
            if project_name and project_name.startswith("["):
                try:
                    parsed_project_name = json.loads(project_name)
                except json.JSONDecodeError:
                    pass  # Use as-is if not valid JSON
            
            # Parse boolean strings
            parsed_error = None
            if error is not None:
                parsed_error = error.lower() == "true" if error.lower() in ("true", "false") else None
            
            parsed_is_root = None
            if is_root is not None:
                if is_root.lower() == "true":
                    parsed_is_root = True
                elif is_root.lower() == "false":
                    parsed_is_root = False
            
            return fetch_runs_tool(
                client,
                project_name=parsed_project_name,
                trace_id=trace_id,
                run_type=run_type,
                error=parsed_error,
                is_root=parsed_is_root,
                filter=filter,
                trace_filter=trace_filter,
                tree_filter=tree_filter,
                order_by=order_by,
                limit=limit,
            )
        except Exception as e:
            return {"error": str(e)}

    # Register project tools
    @mcp.tool()
    def list_projects(limit: int = 5, project_name: str = None, more_info: str = "false", ctx: Context = None) -> Dict[str, Any]:
        """
        List LangSmith projects with optional filtering and detail level control.
        
        Fetches projects from LangSmith, optionally filtering by name and controlling
        the level of detail returned. Can return either simplified project information
        or full project details.
        
        ---
        🧩 PURPOSE
        ----------
        This function provides a convenient way to list and explore LangSmith projects.
        It supports:
        - Filtering projects by name (partial match)
        - Limiting the number of results
        - Choosing between simplified or full project information
        - Automatically extracting deployment IDs from nested project data
        
        ---
        ⚙️ PARAMETERS
        -------------
        limit : int, default 5
            Maximum number of projects to return (as string, e.g., "5"). This can be adjusted by agents
            or users based on their needs.
        
        project_name : str, optional
            Filter projects by name using partial matching. If provided, only projects
            whose names contain this string will be returned.
            Example: `project_name="Chat"` will match "Chat-LangChain", "ChatBot", etc.
        
        more_info : str, default "false"
            Controls the level of detail returned:
            - `"false"` (default): Returns simplified project information with only
            essential fields: `name`, `project_id`, and `agent_deployment_id` (if available)
            - `"true"`: Returns full project details as returned by the LangSmith API
        
        ---
        📤 RETURNS
        ----------
        List[dict]
            A list of project dictionaries. The structure depends on `more_info`:
            
            **When `more_info=False` (simplified):**
            ```python
            [
                {
                    "name": "Chat-LangChain",
                    "project_id": "787d5165-f110-43ff-a3fb-66ea1a70c971",
                    "agent_deployment_id": "deployment-123"  # Only if available
                },
                ...
            ]
            ```
            
            **When `more_info=True` (full details):**
            Returns complete project objects with all fields from the LangSmith API,
            including metadata, settings, statistics, and nested structures.
        
        ---
        🧪 EXAMPLES
        ------------
        1️⃣ **List first 5 projects (simplified)**
        ```python
        projects = list_projects(limit="5")
        ```
        
        2️⃣ **Search for projects with "Chat" in the name**
        ```python
        projects = list_projects(project_name="Chat", limit="10")
        ```
        
        3️⃣ **Get full project details**
        ```python
        projects = list_projects(limit="3", more_info="true")
        ```
        
        4️⃣ **Find a specific project with full details**
        ```python
        projects = list_projects(project_name="MyProject", more_info="true", limit="1")
        ```
        
        ---
        🧠 NOTES FOR AGENTS
        --------------------
        - Use `more_info="false"` for quick project discovery and listing
        - Use `more_info="true"` when you need detailed project information
        - The `agent_deployment_id` field is automatically extracted from nested
        project data when available, making it easy to identify agent deployments
        - Projects are filtered to exclude reference projects by default
        - The function uses `name_contains` for filtering, so partial matches work
        """
        try:
            client = get_client_from_context(ctx)
            parsed_more_info = more_info.lower() == "true"
            return list_projects_tool(client, limit=limit, project_name=project_name, more_info=parsed_more_info)
        except Exception as e:
            return {"error": str(e)}

    # Register dataset tools
    @mcp.tool()
    def list_datasets(
        dataset_ids: Optional[str] = None,
        data_type: Optional[str] = None,
        dataset_name: Optional[str] = None,
        dataset_name_contains: Optional[str] = None,
        metadata: Optional[str] = None,
        limit: int = 20,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        Fetch LangSmith datasets.

        Note: If no arguments are provided, all datasets will be returned.

        Args:
            dataset_ids (Optional[str]): Dataset IDs to filter by as JSON array string (e.g., '["id1", "id2"]') or single ID
            data_type (Optional[str]): Filter by dataset data type (e.g., 'chat', 'kv')
            dataset_name (Optional[str]): Filter by exact dataset name
            dataset_name_contains (Optional[str]): Filter by substring in dataset name
            metadata (Optional[str]): Filter by metadata as JSON object string (e.g., '{"key": "value"}')
            limit (int): Max number of datasets to return (default: 20)
            ctx: FastMCP context (automatically provided)

        Returns:
            Dict[str, Any]: Dictionary containing the datasets and metadata,
                            or an error message if the datasets cannot be retrieved
        """
        try:
            client = get_client_from_context(ctx)
            
            # Parse list strings (JSON arrays)
            parsed_dataset_ids = None
            if dataset_ids is not None:
                try:
                    parsed_dataset_ids = json.loads(dataset_ids) if dataset_ids.startswith("[") else [dataset_ids]
                except (json.JSONDecodeError, AttributeError):
                    parsed_dataset_ids = [dataset_ids] if dataset_ids else None
            
            # Parse metadata (JSON object)
            parsed_metadata = None
            if metadata is not None:
                try:
                    parsed_metadata = json.loads(metadata) if metadata.startswith("{") else None
                except (json.JSONDecodeError, AttributeError):
                    parsed_metadata = None
            
            return list_datasets_tool(
                client,
                dataset_ids=parsed_dataset_ids,
                data_type=data_type,
                dataset_name=dataset_name,
                dataset_name_contains=dataset_name_contains,
                metadata=parsed_metadata,
                limit=limit,
            )
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def list_examples(
        dataset_id: Optional[str] = None,
        dataset_name: Optional[str] = None,
        example_ids: Optional[str] = None,
        filter: Optional[str] = None,
        metadata: Optional[str] = None,
        splits: Optional[str] = None,
        inline_s3_urls: Optional[str] = None,
        include_attachments: Optional[str] = None,
        as_of: Optional[str] = None,
        limit: int = 10,
        offset: Optional[str] = None,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        Fetch examples from a LangSmith dataset with advanced filtering options.

        Note: Either dataset_id, dataset_name, or example_ids must be provided.
        If multiple are provided, they are used in order of precedence: example_ids, dataset_id, dataset_name.

        Args:
            dataset_id (Optional[str]): Dataset ID to retrieve examples from
            dataset_name (Optional[str]): Dataset name to retrieve examples from
            example_ids (Optional[str]): Specific example IDs as JSON array string (e.g., '["id1", "id2"]') or single ID
            limit (int): Maximum number of examples to return (default: 10)
            offset (int): Number of examples to skip (default: 0)
            filter (Optional[str]): Filter string using LangSmith query syntax (e.g., 'has(metadata, {"key": "value"})')
            metadata (Optional[str]): Metadata to filter by as JSON object string (e.g., '{"key": "value"}')
            splits (Optional[str]): Dataset splits as JSON array string (e.g., '["train", "test"]') or single split
            inline_s3_urls (Optional[str]): Whether to inline S3 URLs: "true" or "false" (default: SDK default if not specified)
            include_attachments (Optional[str]): Whether to include attachments: "true" or "false" (default: SDK default if not specified)
            as_of (Optional[str]): Dataset version tag OR ISO timestamp to retrieve examples as of that version/time
            ctx: FastMCP context (automatically provided)

        Returns:
            Dict[str, Any]: Dictionary containing the examples and metadata,
                            or an error message if the examples cannot be retrieved
        """
        try:
            client = get_client_from_context(ctx)
            
            # Parse list strings (JSON arrays)
            parsed_example_ids = None
            if example_ids is not None:
                try:
                    parsed_example_ids = json.loads(example_ids) if example_ids.startswith("[") else [example_ids]
                except (json.JSONDecodeError, AttributeError):
                    parsed_example_ids = [example_ids] if example_ids else None
            
            parsed_splits = None
            if splits is not None:
                try:
                    parsed_splits = json.loads(splits) if splits.startswith("[") else [splits]
                except (json.JSONDecodeError, AttributeError):
                    parsed_splits = [splits] if splits else None
            
            # Parse metadata (JSON object)
            parsed_metadata = None
            if metadata is not None:
                try:
                    parsed_metadata = json.loads(metadata) if metadata.startswith("{") else None
                except (json.JSONDecodeError, AttributeError):
                    parsed_metadata = None
            
            # Parse boolean strings
            parsed_inline_s3_urls = None
            if inline_s3_urls is not None:
                parsed_inline_s3_urls = inline_s3_urls.lower() == "true"
            
            parsed_include_attachments = None
            if include_attachments is not None:
                parsed_include_attachments = include_attachments.lower() == "true"
            
            # Parse integer strings
            parsed_limit = int(limit) if limit else None
            parsed_offset = int(offset) if offset else None
            
            return list_examples_tool(
                client,
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                example_ids=parsed_example_ids,
                filter=filter,
                metadata=parsed_metadata,
                splits=parsed_splits,
                inline_s3_urls=parsed_inline_s3_urls,
                include_attachments=parsed_include_attachments,
                as_of=as_of,
                limit=parsed_limit,
                offset=parsed_offset,
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
