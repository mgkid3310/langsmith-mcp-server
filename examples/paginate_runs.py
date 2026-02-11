"""
Example: Char-based pagination for LangSmith runs (trace-scoped).

Fetches all runs for a trace (up to a safe bound), builds pages by character
budget, and returns the requested page. Stateless, no cursor/offset.

Usage:
    TRACE_ID=<uuid> PROJECT_NAME=default uv run python examples/paginate_runs.py

    # Optional env:
    MAX_CHARS_PER_PAGE=50000
    PREVIEW_CHARS=120   # truncate long strings to this length
"""

import json
import os
import sys

from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_here, ".."))  # project root for langsmith_mcp_server
sys.path.insert(0, _here)  # examples/ for paginate_runs_lib

from langsmith_mcp_server.services.tools.traces import fetch_runs_tool

from paginate_runs_lib import MAX_RUNS_PER_TRACE, paginate_runs_all_pages

api_key = os.getenv("LANGSMITH_API_KEY")
if not api_key:
    print("Set LANGSMITH_API_KEY (e.g. in .env)")
    sys.exit(1)

client = Client(api_key=api_key)


def main() -> None:
    trace_id = os.getenv("TRACE_ID")
    project_name = os.getenv("PROJECT_NAME", "default")
    max_chars_per_page = int(os.getenv("MAX_CHARS_PER_PAGE", "50000"))
    preview_chars = int(os.getenv("PREVIEW_CHARS", "0"))

    if not trace_id:
        print("Set TRACE_ID (UUID of the trace).")
        print("Example: TRACE_ID=019c49bc-11c6-7803-9d6a-8a1842915d1f uv run python examples/paginate_runs.py")
        sys.exit(1)

    # Fetch all runs for the trace (stable order, up to safe bound)
    result = fetch_runs_tool(
        client,
        project_name=project_name,
        trace_id=trace_id,
        order_by="-start_time",
        limit=MAX_RUNS_PER_TRACE,
    )

    if "error" in result:
        print("Error:", result["error"])
        sys.exit(1)

    runs_dict = result["runs"]

    # Build all pages and save one file per page
    all_pages = paginate_runs_all_pages(
        runs_dict,
        max_chars_per_page=max_chars_per_page,
        preview_chars=preview_chars,
    )

    total_pages = len(all_pages)
    print(f"Total pages: {total_pages} (max_chars_per_page={max_chars_per_page}, preview_chars={preview_chars})")

    for out in all_pages:
        page_num = out["page_number"]
        out_path = os.path.join(_here, f"paginate_runs_page_{page_num}.json")
        with open(out_path, "w") as f:
            json.dump(out, f, indent=2, default=str)
        size = len(json.dumps(out, indent=2, default=str))
        print(f"  Page {page_num}: {len(out['runs'])} run(s), {size} chars -> {out_path}")


if __name__ == "__main__":
    main()
