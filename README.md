# 🦜🛠️ LangSmith MCP Server

> [!WARNING]
> LangSmith MCP Server is under active development and many features are not yet implemented.


![LangSmith MCP Hero](https://raw.githubusercontent.com/langchain-ai/langsmith-mcp-server/refs/heads/main/docs/assets/langsmith_mcp_hero.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)

A production-ready [Model Context Protocol](https://modelcontextprotocol.io/introduction) (MCP) server that provides seamless integration with the [LangSmith](https://smith.langchain.com) observability platform. This server enables language models to fetch conversation history and prompts from LangSmith.

## 📋 Overview

The LangSmith MCP Server bridges the gap between language models and the LangSmith platform, enabling advanced capabilities for conversation tracking, prompt management, and analytics integration.

## 🛠️ Installation Options

### 📝 General Prerequisites

1. Install [uv](https://github.com/astral-sh/uv) (a fast Python package installer and resolver):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone this repository and navigate to the project directory:
   ```bash
   git clone https://github.com/langchain-ai/langsmith-mcp-server.git
   cd langsmith-mcp-server
   ```

### 🔌 MCP Client Integration

Once you have the LangSmith MCP Server, you can integrate it with various MCP-compatible clients. You have two installation options:

#### 📦 From PyPI

1. Install the package:
   ```bash
   uv run pip install --upgrade langsmith-mcp-server
   ```

2. Add to your client MCP config:
   ```json
   {
       "mcpServers": {
           "LangSmith API MCP Server": {
               "command": "/path/to/uvx",
               "args": [
                   "langsmith-mcp-server"
               ],
               "env": {
                   "LANGSMITH_API_KEY": "your_langsmith_api_key",
                   "LANGSMITH_WORKSPACE_ID": "your_workspace_id",
                   "LANGSMITH_ENDPOINT": "https://api.smith.langchain.com"
               }
           }
       }
   }
   ```

#### ⚙️ From Source

Add the following configuration to your MCP client settings:

```json
{
    "mcpServers": {
        "LangSmith API MCP Server": {
            "command": "/path/to/uv",
            "args": [
                "--directory",
                "/path/to/langsmith-mcp-server/langsmith_mcp_server",
                "run",
                "server.py"
            ],
            "env": {
                "LANGSMITH_API_KEY": "your_langsmith_api_key",
                "LANGSMITH_WORKSPACE_ID": "your_workspace_id",
                "LANGSMITH_ENDPOINT": "https://api.smith.langchain.com"
            }
        }
    }
}
```

Replace the following placeholders:
- `/path/to/uv`: The absolute path to your uv installation (e.g., `/Users/username/.local/bin/uv`). You can find it running `which uv`.
- `/path/to/langsmith-mcp-server`: The absolute path to your langsmith-mcp project directory
- `your_langsmith_api_key`: Your LangSmith API key (required)
- `your_workspace_id`: Your LangSmith workspace ID (optional, for API keys scoped to multiple workspaces)
- `https://api.smith.langchain.com`: The LangSmith API endpoint (optional, defaults to the standard endpoint)

Example configuration:
```json
{
    "mcpServers": {
        "LangSmith API MCP Server": {
            "command": "/Users/mperini/.local/bin/uvx",
            "args": [
                "langsmith-mcp-server"
            ],
            "env": {
                "LANGSMITH_API_KEY": "lsv2_pt_1234",
                "LANGSMITH_WORKSPACE_ID": "your_workspace_id",
                "LANGSMITH_ENDPOINT": "https://api.smith.langchain.com"
            }
        }
    }
}
```

Copy this configuration in Cursor > MCP Settings.

![LangSmith Cursor Integration](docs/assets/cursor_mcp.png)

### 🔧 Environment Variables

The LangSmith MCP Server supports the following environment variables:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `LANGSMITH_API_KEY` | ✅ Yes | Your LangSmith API key for authentication | `lsv2_pt_1234567890` |
| `LANGSMITH_WORKSPACE_ID` | ❌ No | Workspace ID for API keys scoped to multiple workspaces | `your_workspace_id` |
| `LANGSMITH_ENDPOINT` | ❌ No | Custom API endpoint URL (for self-hosted or EU region) | `https://api.smith.langchain.com` |

**Notes:**
- Only `LANGSMITH_API_KEY` is required for basic functionality
- `LANGSMITH_WORKSPACE_ID` is useful when your API key has access to multiple workspaces
- `LANGSMITH_ENDPOINT` allows you to use custom endpoints for self-hosted LangSmith installations or the EU region

## 🐳 Docker Deployment (HTTP-Streamable)

The LangSmith MCP Server can be deployed as an HTTP server using Docker, enabling remote access via the HTTP-streamable protocol.

### Building the Docker Image

```bash
docker build -t langsmith-mcp-server .
```

### Running with Docker

```bash
docker run -p 8000:8000 langsmith-mcp-server
```

The API key is provided via the `LANGSMITH-API-KEY` header when connecting, so no environment variables are required for HTTP-streamable protocol.

### Connecting with HTTP-Streamable Protocol

Once the Docker container is running, you can connect to it using the HTTP-streamable transport. The server accepts authentication via headers:

**Required header:**
- `LANGSMITH-API-KEY`: Your LangSmith API key

**Optional headers:**
- `LANGSMITH-WORKSPACE-ID`: Workspace ID for API keys scoped to multiple workspaces
- `LANGSMITH-ENDPOINT`: Custom endpoint URL (for self-hosted or EU region)

**Example client configuration:**
```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

headers = {
    "LANGSMITH-API-KEY": "lsv2_pt_your_api_key_here",
    # Optional:
    # "LANGSMITH-WORKSPACE-ID": "your_workspace_id",
    # "LANGSMITH-ENDPOINT": "https://api.smith.langchain.com",
}

async with streamablehttp_client("http://localhost:8000/mcp", headers=headers) as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        # Use the session to call tools, list prompts, etc.
```

### Cursor Integration

To add the LangSmith MCP Server to Cursor using HTTP-streamable protocol, add the following to your `mcp.json` configuration file:

```json
{
  "mcpServers": {
    "HTTP-Streamable LangSmith MCP Server": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "LANGSMITH-API-KEY": "lsv2_pt_your_api_key_here"
      }
    }
  }
}
```

**Optional headers:**
```json
{
  "mcpServers": {
    "HTTP-Streamable LangSmith MCP Server": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "LANGSMITH-API-KEY": "lsv2_pt_your_api_key_here",
        "LANGSMITH-WORKSPACE-ID": "your_workspace_id",
        "LANGSMITH-ENDPOINT": "https://api.smith.langchain.com"
      }
    }
  }
}
```

Make sure the server is running before connecting Cursor to it.

### Health Check

The server provides a health check endpoint:
```bash
curl http://localhost:8000/health
```

This endpoint does not require authentication and returns `"LangSmith MCP server is running"` when the server is healthy.

## 🧪 Development and Contributing 🤝

If you want to develop or contribute to the LangSmith MCP Server, follow these steps:

1. Create a virtual environment and install dependencies:
   ```bash
   uv sync
   ```

2. To include test dependencies:
   ```bash
   uv sync --group test
   ```

3. View available MCP commands:
   ```bash
   uvx langsmith-mcp-server
   ```

4. For development, run the MCP inspector:
   ```bash
   uv run mcp dev langsmith_mcp_server/server.py
   ```
   - This will start the MCP inspector on a network port
   - Install any required libraries when prompted
   - The MCP inspector will be available in your browser
   - Set the `LANGSMITH_API_KEY` environment variable in the inspector
   - Connect to the server
   - Navigate to the "Tools" tab to see all available tools

5. Before submitting your changes, run the linting and formatting checks:
   ```bash
   make lint
   make format
   ```

## 🚀 Example Use Cases

The server enables powerful capabilities including:

- 💬 **Conversation History**: "Fetch the history of my conversation with the AI assistant from thread 'thread-123' in project 'my-chatbot'"
- 📚 **Prompt Management**: "Get all public prompts in my workspace"
- 🔍 **Smart Search**: "Find private prompts containing the word 'joke'"
- 📝 **Template Access**: "Pull the template for the 'legal-case-summarizer' prompt"
- 🔧 **Configuration**: "Get the system message from a specific prompt template"

## 🛠️ Available Tools

The LangSmith MCP Server provides the following tools for integration with LangSmith:

| Tool Name | Description |
|-----------|-------------|
| `list_prompts` | Fetch prompts from LangSmith with optional filtering. Filter by visibility (public/private) and limit results. |
| `get_prompt_by_name` | Get a specific prompt by its exact name, returning the prompt details and template. |
| `get_thread_history` | Retrieve the message history for a specific conversation thread, returning messages in chronological order. |
| `get_project_runs_stats` | Get statistics about runs in a LangSmith project, either for the last run or overall project stats. |
| `fetch_trace` | Fetch trace content for debugging and analyzing LangSmith runs using project name or trace ID. |
| `list_datasets` | Fetch LangSmith datasets with filtering options by ID, type, name, or metadata. |
| `list_examples` | Fetch examples from a LangSmith dataset with advanced filtering options. |
| `read_dataset` | Read a specific dataset from LangSmith using dataset ID or name. |
| `read_example` | Read a specific example from LangSmith using the example ID and optional version information. |

## 📄 License

This project is distributed under the MIT License. For detailed terms and conditions, please refer to the LICENSE file.


Made with ❤️ by the [LangChain](https://langchain.com) Team
