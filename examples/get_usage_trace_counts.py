"""
Fetch LangSmith trace/usage counts via the billing APIs.

This example demonstrates two ways to get trace usage information:

1. **Organization billing usage** (self-hosted and cloud)
   - Endpoint: GET /api/v1/orgs/current/billing/usage
   - Returns organization-level trace counts for a date range.
   - Docs: https://docs.langchain.com/langsmith/self-host-organization-charts

2. **Granular billable usage** (cloud from 2026-01-05; self-hosted when enabled)
   - Endpoint: GET /api/v1/orgs/current/billing/granular-usage
   - Returns trace counts grouped by workspace, project, user, or API key.
   - Requires organization:read and workspace_ids.
   - Docs: https://docs.langchain.com/langsmith/granular-usage

Both APIs are REST-only (not in the LangSmith Python SDK), so this example
uses direct HTTP calls with urllib.
"""

from __future__ import annotations

import copy
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Configuration from environment (same as other examples)
API_KEY = os.getenv("LANGSMITH_API_KEY")
ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com").rstrip("/")


def _request(path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    """Send GET request to LangSmith API with API key."""
    if not API_KEY:
        return {"error": "LANGSMITH_API_KEY is not set"}
    url = f"{ENDPOINT}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/json")
    req.add_header("X-API-Key", API_KEY)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": f"HTTP {e.code}: {body}"}
    except OSError as e:
        return {"error": str(e)}


def list_workspaces() -> dict[str, Any]:
    """
    List all workspaces for the current org (single API call).

    Returns:
        Response from GET /api/v1/workspaces (list of workspace objects with id, display_name, etc.).
    """
    return _request("/api/v1/workspaces")


def get_workspace_by_id(workspace_id: str) -> dict[str, Any]:
    """
    Fetch a single workspace by UUID (single API call).

    Returns:
        Response from GET /api/v1/workspaces/{workspace_id}, or error dict.
    """
    return _request(f"/api/v1/workspaces/{workspace_id}")


def _build_workspace_id_to_name(
    single_workspace: str | None,
) -> dict[str, str]:
    """
    Build workspace_id -> name map. If single_workspace is set (uuid or name),
    fetch only that workspace; otherwise list all (one call each).
    """
    id_to_name: dict[str, str] = {}
    if single_workspace:
        single_workspace = single_workspace.strip()
        # UUID-like: try single-workspace endpoint first
        if len(single_workspace) == 36 and single_workspace.count("-") == 4:
            resp = get_workspace_by_id(single_workspace)
            if isinstance(resp, dict) and "error" not in resp and resp.get("id"):
                name = resp.get("display_name") or resp.get("name") or single_workspace
                id_to_name[str(resp["id"])] = name
                return id_to_name
        # Name or single-get failed: list and filter
        ws_resp = list_workspaces()
        workspaces: list[dict] = []
        if isinstance(ws_resp, list):
            workspaces = [w for w in ws_resp if isinstance(w, dict)]
        elif isinstance(ws_resp, dict) and "error" not in ws_resp:
            workspaces = list(ws_resp.get("workspaces") or ws_resp.get("items") or [])
        single_lower = single_workspace.lower()
        for w in workspaces:
            if not w.get("id"):
                continue
            wid = str(w["id"])
            name = w.get("display_name") or w.get("name") or wid
            if wid == single_workspace or (name or "").lower() == single_lower:
                id_to_name[wid] = name
                return id_to_name
        return id_to_name
    # All workspaces: one list call
    ws_resp = list_workspaces()
    if isinstance(ws_resp, list):
        for w in ws_resp:
            if isinstance(w, dict) and w.get("id"):
                id_to_name[str(w["id"])] = (
                    w.get("display_name") or w.get("name") or str(w["id"])
                )
    elif isinstance(ws_resp, dict) and "error" not in ws_resp:
        for w in (ws_resp.get("workspaces") or ws_resp.get("items") or []):
            if isinstance(w, dict) and w.get("id"):
                id_to_name[str(w["id"])] = (
                    w.get("display_name") or w.get("name") or str(w["id"])
                )
    return id_to_name


def _augment_usage_groups_with_names(
    usage: list[dict],
    workspace_id_to_name: dict[str, str],
    only_workspace_id: str | None = None,
) -> list[dict]:
    """
    Modify usage: each metric's groups becomes
    { uuid: { "workspace_name": "<name>", "value": <number> } }.
    If only_workspace_id is set, only that workspace is kept in each groups dict.
    """
    result = copy.deepcopy(usage)
    for item in result:
        groups = (item or {}).get("groups")
        if not isinstance(groups, dict):
            continue
        new_groups: dict[str, Any] = {}
        for uid, val in groups.items():
            if only_workspace_id and uid != only_workspace_id:
                continue
            name = workspace_id_to_name.get(uid) or uid
            new_groups[uid] = {"workspace_name": name, "value": val}
        item["groups"] = new_groups
    return result


def get_org_billing_usage(
    starting_on: str,
    ending_before: str,
    on_current_plan: bool = True,
) -> dict[str, Any]:
    """
    Fetch organization-level trace counts (billing usage).

    Used for "Usage by Workspace" and "Organization Usage" style metrics.
    Works with both LangSmith Cloud and self-hosted (when using an online key).

    Args:
        starting_on: Start of range (ISO 8601), e.g. "2025-09-01T00:00:00Z"
        ending_before: End of range (ISO 8601), e.g. "2025-10-01T00:00:00Z"
        on_current_plan: If true, only include usage on the current plan.

    Returns:
        Response from GET /api/v1/orgs/current/billing/usage
    """
    params = {
        "starting_on": starting_on,
        "ending_before": ending_before,
        "on_current_plan": "true" if on_current_plan else "false",
    }
    return _request("/api/v1/orgs/current/billing/usage", params)


def get_granular_usage(
    start_time: str,
    end_time: str,
    workspace_ids: list[str],
    group_by: str = "workspace",
) -> dict[str, Any]:
    """
    Fetch granular billable usage (trace counts by dimension).

    Group by: workspace, project, user, or api_key.
    Requires organization:read. For Cloud, data from 2026-01-05 onward.

    Args:
        start_time: Start of range (ISO 8601).
        end_time: End of range (ISO 8601).
        workspace_ids: List of workspace UUIDs to include (required).
        group_by: One of workspace, project, user, api_key.

    Returns:
        Response with "stride" and "usage" (list of time_bucket, dimensions, traces).
    """
    if not workspace_ids:
        return {"error": "workspace_ids is required for granular usage"}
    params = {
        "start_time": start_time,
        "end_time": end_time,
        "group_by": group_by,
    }
    # API expects workspace_ids as repeated query param
    query = urllib.parse.urlencode(params)
    for wid in workspace_ids:
        query += "&" + urllib.parse.urlencode({"workspace_ids": wid})
    return _request("/api/v1/orgs/current/billing/granular-usage?" + query)


def main() -> None:
    # Optional: single workspace by uuid or name (fetch only that one)
    single_workspace = os.getenv("LANGSMITH_WORKSPACE", "").strip() or None

    # Default: last 30 days
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=30)
    start_str = start.isoformat().replace("+00:00", "Z")
    end_str = end.isoformat().replace("+00:00", "Z")

    print("1. Organization billing usage (trace counts for date range)")
    if single_workspace:
        print(f"   Single workspace: {single_workspace}")
    print(f"   Range: {start_str} -> {end_str}")
    usage = get_org_billing_usage(start_str, end_str)
    if isinstance(usage, dict) and "error" in usage:
        print(f"   Error: {usage['error']}")
    elif isinstance(usage, list) and usage:
        workspace_id_to_name = _build_workspace_id_to_name(single_workspace)
        only_workspace_id: str | None = None
        if single_workspace and workspace_id_to_name:
            only_workspace_id = next(iter(workspace_id_to_name.keys()), None)
        augmented = _augment_usage_groups_with_names(
            usage, workspace_id_to_name, only_workspace_id
        )
        print(json.dumps(augmented, indent=2))

        # Verify: groups keys = workspace_id; optional granular section (console only)
        one_workspace_id: str | None = only_workspace_id
        if not one_workspace_id:
            for item in augmented:
                groups = (item or {}).get("groups") or {}
                if isinstance(groups, dict) and groups:
                    one_workspace_id = next(iter(groups.keys()))
                    break
        if one_workspace_id:
            print("\n   Verify: groups keys = workspace_id (tenant_id). Fetching granular usage for one:")
            print(f"   workspace_id = {one_workspace_id}")
            verify = get_granular_usage(
                start_time=start_str,
                end_time=end_str,
                workspace_ids=[one_workspace_id],
                group_by="workspace",
            )
            if "error" in verify:
                print(f"   Verification result: {verify['error']}")
            else:
                ul = verify.get("usage", [])
                print(f"   Verification OK: granular API returned {len(ul)} record(s) for this workspace_id.")
                if ul:
                    rec = ul[0]
                    print(f"   Sample: time_bucket={rec.get('time_bucket')} dimensions={rec.get('dimensions')} traces={rec.get('traces')}")

        workspace_ids_str = os.getenv("LANGSMITH_WORKSPACE_IDS", "")
        workspace_ids = [w.strip() for w in workspace_ids_str.split(",") if w.strip()]
        if not workspace_ids and one_workspace_id:
            workspace_ids = [one_workspace_id]
        if workspace_ids:
            print("\n2. Granular usage (by workspace)")
            granular = get_granular_usage(
                start_time=start_str, end_time=end_str,
                workspace_ids=workspace_ids, group_by="workspace",
            )
            if "error" in granular:
                print(f"   Error: {granular['error']}")
            else:
                for record in granular.get("usage", [])[:10]:
                    dims = record.get("dimensions", {})
                    tb = record.get("time_bucket", "")
                    traces = record.get("traces", 0)
                    print(f"   {tb}: {dims} -> {traces} traces")
                if len(granular.get("usage", [])) > 10:
                    print("   ...")
        else:
            print("\n2. Granular usage skipped (set LANGSMITH_WORKSPACE_IDS to enable)")

        # Export: only the modified usage (no workspace_id_to_name, no granular_usage)
        output_path = os.path.join(os.path.dirname(__file__), "usage_trace_counts_result.json")
        with open(output_path, "w") as f:
            json.dump(augmented, f, indent=2)
        print(f"\nFull result written to {output_path}")


if __name__ == "__main__":
    main()
