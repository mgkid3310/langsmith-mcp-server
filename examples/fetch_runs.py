"""
Example: Call fetch_runs_tool locally.

Fetches runs from LangSmith for a project (and optional trace_id).
Requires LANGSMITH_API_KEY in the environment. Result is saved as pretty-printed JSON.

Usage:
    uv run python examples/fetch_runs.py

    PROJECT_NAME=my-chat LIMIT=10 uv run python examples/fetch_runs.py
    TRACE_ID=019c49af-ca90-7cb1-87ac-78729c87af8d uv run python examples/fetch_runs.py
"""

import json
import os
import sys

from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langsmith_mcp_server.services.tools.traces import fetch_runs_tool

api_key = os.getenv("LANGSMITH_API_KEY")
if not api_key:
    print("Set LANGSMITH_API_KEY (e.g. in .env)")
    sys.exit(1)

client = Client(api_key=api_key)


def main() -> None:
    project_name = os.getenv("PROJECT_NAME", "default")
    trace_id = os.getenv("TRACE_ID")
    limit = int(os.getenv("LIMIT", "5"))

    print(f"Fetching runs: project={project_name!r}, trace_id={trace_id or 'all'}, limit={limit}")

    result = fetch_runs_tool(
        client,
        project_name=project_name,
        trace_id=trace_id,
        is_root=True,
        limit=limit,
    )

    if "error" in result:
        print("Error:", result["error"])
        return

    runs = result.get("runs", [])
    print(f"Fetched {len(runs)} run(s)")
    for i, run in enumerate(runs[:3]):
        run_id = run.get("id", "?")
        run_type = run.get("run_type", "?")
        print(f"  {i + 1}. id={run_id} run_type={run_type}")
    if len(runs) > 3:
        print(f"  ... and {len(runs) - 3} more")

    out_path = os.path.join(os.path.dirname(__file__), "fetch_runs_result.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"Result saved to {out_path}")


if __name__ == "__main__":
    main()
