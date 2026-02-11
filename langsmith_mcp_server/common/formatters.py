"""Output formatting utilities for messages and runs."""

import json
from typing import Any, Dict, List


def format_messages(messages: List[Dict[str, Any]]) -> str:
    """
    Format messages as pretty-printed JSON.

    Args:
        messages: List of message dictionaries

    Returns:
        JSON string (indent=2) representation of messages
    """
    return json.dumps(messages, indent=2, default=str, ensure_ascii=False)


def _extract_messages_from_dict(
    data: Any, path: str = "", depth: int = 0, max_depth: int = 5
) -> List[Dict[str, Any]]:
    """
    Recursively extract messages from nested dictionary structures.

    Args:
        data: Dictionary, list, or other data structure to search
        path: Current path in the structure (for debugging)
        depth: Current recursion depth
        max_depth: Maximum recursion depth to avoid infinite loops

    Returns:
        List of message dictionaries found
    """
    if depth > max_depth:
        return []

    messages = []

    if isinstance(data, dict):
        # Check for messages key directly (highest priority)
        if "messages" in data:
            msgs = data["messages"]
            if isinstance(msgs, list):
                # Found messages list - extract and return (don't recurse further)
                for msg in msgs:
                    if isinstance(msg, dict):
                        messages.append(msg)
                return messages  # Return early since we found messages

        # Check for single message key
        if "message" in data:
            msg = data["message"]
            if isinstance(msg, dict):
                messages.append(msg)

        # Check for OpenAI-style choices
        if "choices" in data:
            choices = data["choices"]
            if isinstance(choices, list):
                for choice in choices:
                    if isinstance(choice, dict) and "message" in choice:
                        messages.append(choice["message"])

        # If we found messages at this level, return them (don't recurse)
        if messages:
            return messages

        # Recursively search nested dictionaries
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                nested_msgs = _extract_messages_from_dict(
                    value, f"{path}.{key}", depth + 1, max_depth
                )
                messages.extend(nested_msgs)

    elif isinstance(data, list):
        # Search each item in the list
        for item in data:
            if isinstance(item, (dict, list)):
                nested_msgs = _extract_messages_from_dict(item, f"{path}[]", depth + 1, max_depth)
                messages.extend(nested_msgs)

    return messages


def extract_messages_from_run(run_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract messages from a run dictionary.

    Messages can be in various locations:
    - run.inputs.messages (for LLM runs)
    - run.outputs.messages (for some run types)
    - run.outputs.output.messages (for nested output structures)
    - run.outputs.choices[0].message (for OpenAI-style outputs)

    Args:
        run_dict: Run dictionary from LangSmith

    Returns:
        List of message dictionaries
    """
    messages = []

    # Check inputs for messages
    inputs = run_dict.get("inputs")
    if inputs is not None:
        input_messages = _extract_messages_from_dict(inputs, "inputs")
        messages.extend(input_messages)

    # Check outputs for messages (including nested structures)
    outputs = run_dict.get("outputs")
    if outputs is not None:
        output_messages = _extract_messages_from_dict(outputs, "outputs")
        messages.extend(output_messages)

    # Filter to ensure we only return message dictionaries
    # Sometimes messages might be in unexpected formats
    valid_messages = []
    seen_ids = set()  # Deduplicate messages by ID if present
    for msg in messages:
        if isinstance(msg, dict):
            # Deduplicate by message ID if available
            msg_id = msg.get("id")
            if msg_id and msg_id in seen_ids:
                continue
            if msg_id:
                seen_ids.add(msg_id)
            valid_messages.append(msg)
        # Skip non-dict messages (lists, strings, etc.)

    return valid_messages


def format_runs_with_messages(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract messages from runs and return pretty-printed JSON in "formatted".
    """
    all_messages = []
    for run in runs:
        run_messages = extract_messages_from_run(run)
        if run_messages:
            all_messages.extend(run_messages)
    return {"formatted": format_messages(all_messages)}
