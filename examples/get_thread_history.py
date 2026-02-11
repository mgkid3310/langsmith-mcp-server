"""
Example: Fetch conversation thread history from LangSmith.

Retrieves the message history for a specific thread in a project.
Requires LANGSMITH_API_KEY in the environment (e.g. via .env).

Usage:
    # Set thread_id and project_name to match your LangSmith data.
    # Thread IDs often come from metadata (session_id, conversation_id, or thread_id).
    uv run python examples/get_thread_history.py

    # Or with explicit env:
    LANGSMITH_API_KEY=lsv2_pt_... uv run python examples/get_thread_history.py
"""

import json
import os
import sys

from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

# Add project root for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langsmith_mcp_server.services.tools.traces import get_thread_history_tool

api_key = os.getenv("LANGSMITH_API_KEY")
client = Client(api_key=api_key)


def main() -> None:
    # Replace with a real thread_id and project_name from your LangSmith workspace.
    # You can get thread_id from a trace (e.g. fetch_trace output) or from your app's metadata.
    thread_id = os.getenv("THREAD_ID", "your-thread-id")
    project_name = os.getenv("PROJECT_NAME", "your-project-name")

    if thread_id == "your-thread-id" or project_name == "your-project-name":
        print(
            "Set THREAD_ID and PROJECT_NAME (env or edit this script).\n"
            "Example: THREAD_ID=abc-123 PROJECT_NAME=MyChat uv run python examples/get_thread_history.py"
        )
        return

    page_number = int(os.getenv("PAGE_NUMBER", "1"))
    max_chars_per_page = int(os.getenv("MAX_CHARS_PER_PAGE", "25000"))
    preview_chars = int(os.getenv("PREVIEW_CHARS", "150"))

    result = get_thread_history_tool(
        client,
        thread_id=thread_id,
        project_name=project_name,
        page_number=page_number,
        max_chars_per_page=max_chars_per_page,
        preview_chars=preview_chars,
    )

    if "error" in result:
        print("Error:", result["error"])
        return

    out_path = os.path.join(os.path.dirname(__file__), "thread_history_result.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Thread history saved to {out_path}")
    print(
        f"Page {result.get('page_number', 1)} of {result.get('total_pages', 1)}, "
        f"messages in this page: {len(result.get('result', []))}, "
        f"max_chars_per_page={result.get('max_chars_per_page')}, preview_chars={result.get('preview_chars')}"
    )


if __name__ == "__main__":
    main()
