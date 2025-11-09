"""Tools for interacting with LangSmith experiments."""

from typing import Any, Dict, Optional
from langsmith import Client
from langsmith_mcp_server.common.helpers import find_in_dict


def list_experiments_tool(
    client: Client,
    reference_dataset_id: Optional[str] = None,
    reference_dataset_name: Optional[str] = None,
    limit: int = 5,
    project_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List LangSmith experiment projects (reference projects) with mandatory dataset filtering.

    Args:
        client: LangSmith client instance
        reference_dataset_id: The ID of the reference dataset to filter experiments by
        reference_dataset_name: The name of the reference dataset to filter experiments by
        limit: Maximum number of experiments to return (default: 5)
        project_name: Filter projects by name using partial matching

    Returns:
        Dictionary containing an "experiments" key with a list of simplified experiment project dictionaries
    """
    # Validate that exactly one of reference_dataset_id or reference_dataset_name is provided
    if reference_dataset_id is None and reference_dataset_name is None:
        raise ValueError(
            "Either 'reference_dataset_id' or 'reference_dataset_name' must be provided"
        )
    if reference_dataset_id is not None and reference_dataset_name is not None:
        raise ValueError(
            "Cannot provide both 'reference_dataset_id' and 'reference_dataset_name'. "
            "Please provide only one."
        )

    projects = []
    for project in client.list_projects(
        reference_free=False,
        reference_dataset_id=reference_dataset_id,
        reference_dataset_name=reference_dataset_name,
        name_contains=project_name,
        limit=limit,
        include_stats=True,
    ):
        projects.append(project.dict())

    simple_projects = []
    for project in projects:
        deployment_id = find_in_dict(project, "deployment_id")
        project_id = project.get("id", None)

        # Extract and format latency (p50 and p99)
        latency_p50 = project.get("latency_p50", None)
        latency_p99 = project.get("latency_p99", None)

        # Extract and format cost (convert Decimal to float for JSON serialization)
        total_cost = project.get("total_cost", None)
        prompt_cost = project.get("prompt_cost", None)
        completion_cost = project.get("completion_cost", None)

        project_dict = {
            "name": project.get("name", None),
            "experiment_id": str(project_id) if project_id is not None else None,
            "feedback_stats": project.get("feedback_stats", None),
        }

        # Add latency metrics if available
        if latency_p50 is not None:
            # Convert timedelta to total seconds (float)
            project_dict["latency_p50_seconds"] = latency_p50.total_seconds()
        if latency_p99 is not None:
            project_dict["latency_p99_seconds"] = latency_p99.total_seconds()

        # Add cost metrics if available
        if total_cost is not None:
            project_dict["total_cost"] = float(total_cost)
        if prompt_cost is not None:
            project_dict["prompt_cost"] = float(prompt_cost)
        if completion_cost is not None:
            project_dict["completion_cost"] = float(completion_cost)

        if deployment_id:
            project_dict["agent_deployment_id"] = deployment_id
        simple_projects.append(project_dict)

    return {"experiments": simple_projects}

