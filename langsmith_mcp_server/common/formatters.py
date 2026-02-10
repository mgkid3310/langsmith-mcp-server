"""Output formatting utilities for messages and runs."""

import json
from typing import Any, Dict, List


def format_messages(messages: List[Dict[str, Any]], format_type: str) -> str:
    """
    Format messages according to the specified format.

    Args:
        messages: List of message dictionaries
        format_type: Output format ('raw', 'json', or 'pretty')

    Returns:
        Formatted string representation of messages
    """
    if format_type == "raw":
        return _format_raw(messages)
    elif format_type == "json":
        return _format_json(messages)
    elif format_type == "pretty":
        return _format_pretty(messages)
    else:
        raise ValueError(f"Unknown format type: {format_type}")


def _format_raw(messages: List[Dict[str, Any]]) -> str:
    """Format as raw JSON (compact)."""
    return json.dumps(messages, default=str, ensure_ascii=False)


def _format_json(messages: List[Dict[str, Any]]) -> str:
    """Format as pretty-printed JSON."""
    return json.dumps(messages, indent=2, default=str, ensure_ascii=False)


def _format_pretty(messages: List[Dict[str, Any]]) -> str:
    """Format as human-readable structured text focusing on conversational exchanges."""
    if not messages:
        return "No messages found."

    output_parts = []

    # Add header
    output_parts.append("=" * 80)
    output_parts.append("CONVERSATION MESSAGES")
    output_parts.append("=" * 80)
    output_parts.append("")

    for i, msg in enumerate(messages, 1):
        msg_type = msg.get("type") or msg.get("role", "unknown")

        # Normalize message type for better display
        type_display = msg_type.upper()
        if type_display == "USER":
            type_display = "👤 HUMAN"
        elif type_display == "ASSISTANT" or type_display == "AI":
            type_display = "🤖 AI"
        elif type_display == "SYSTEM":
            type_display = "⚙️  SYSTEM"
        elif type_display == "TOOL":
            type_display = "🔧 TOOL"
        else:
            type_display = f"📝 {type_display}"

        # Create message header with better formatting
        output_parts.append("─" * 80)
        output_parts.append(f"{type_display} (Message {i})")
        output_parts.append("─" * 80)

        # Format content based on message type
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])
        name = msg.get("name")

        # Handle tool responses - show tool name more prominently
        if msg_type == "tool" and name:
            # Don't duplicate tool name if it's already in the header
            pass

        # Format main content
        if isinstance(content, str):
            if content.strip():
                output_parts.append("")
                # Truncate very long content (e.g., tool responses with large JSON)
                content_str = content.strip()
                max_length = 1500  # Max characters before truncation for better readability
                if len(content_str) > max_length:
                    truncated = content_str[:max_length]
                    remaining = len(content_str) - max_length
                    output_parts.append(truncated)
                    output_parts.append(f"\n... (truncated {remaining:,} more characters)")
                else:
                    output_parts.append(content_str)
            else:
                output_parts.append("(No text content)")
        elif isinstance(content, list):
            # Handle structured content (tool calls, etc.)
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if "text" in item:
                        text_parts.append(item["text"])
                    elif "type" in item:
                        if item["type"] == "tool_use":
                            tool_name = item.get("name", "unknown")
                            tool_input = item.get("input", {})
                            text_parts.append(f"\n[Tool Call: {tool_name}]")
                            if tool_input:
                                text_parts.append(
                                    f"Input: {json.dumps(tool_input, indent=2, default=str)}"
                                )
                        elif item["type"] == "image_url" and "image_url" in item:
                            text_parts.append(f"[Image: {item['image_url'].get('url', 'N/A')}]")
                        else:
                            text_parts.append(json.dumps(item, indent=2, default=str))
                else:
                    text_parts.append(str(item))

            if text_parts:
                output_parts.append("")
                output_parts.append("\n".join(text_parts))
            else:
                output_parts.append("(Structured content with no text)")
        elif content:
            output_parts.append("")
            output_parts.append(str(content))
        else:
            output_parts.append("(No content)")

        # Handle tool calls (OpenAI-style format)
        if tool_calls:
            output_parts.append("")
            if len(tool_calls) == 1:
                output_parts.append("Tool Call:")
            else:
                output_parts.append(f"Tool Calls ({len(tool_calls)}):")
            for idx, tool_call in enumerate(tool_calls, 1):
                if isinstance(tool_call, dict):
                    func = tool_call.get("function", {})
                    tool_name = func.get("name", "unknown")
                    tool_args = func.get("arguments", "")

                    if len(tool_calls) == 1:
                        output_parts.append(f"  → {tool_name}()")
                    else:
                        output_parts.append(f"  {idx}. {tool_name}()")
                    if tool_args:
                        if isinstance(tool_args, str):
                            try:
                                # Try to parse and pretty-print JSON arguments
                                parsed = json.loads(tool_args)
                                args_str = json.dumps(parsed, indent=4, default=str)
                                # Truncate very long arguments
                                if len(args_str) > 400:
                                    args_str = (
                                        args_str[:400]
                                        + f"\n     ... (truncated {len(args_str) - 400:,} more characters)"
                                    )
                                output_parts.append(f"     {args_str}")
                            except (json.JSONDecodeError, TypeError):
                                # Truncate string arguments too
                                if len(tool_args) > 400:
                                    output_parts.append(f"     {tool_args[:400]}... (truncated)")
                                else:
                                    output_parts.append(f"     {tool_args}")
                        else:
                            args_str = json.dumps(tool_args, indent=4, default=str)
                            if len(args_str) > 400:
                                args_str = (
                                    args_str[:400]
                                    + f"\n     ... (truncated {len(args_str) - 400:,} more characters)"
                                )
                            output_parts.append(f"     {args_str}")

        # Handle additional metadata (only show for debugging, commented out for cleaner output)
        # if msg.get("id"):
        #     output_parts.append(f"\n[Message ID: {msg['id']}]")

        output_parts.append("")  # Empty line between messages

    output_parts.append("=" * 80)
    output_parts.append(f"Total: {len(messages)} message(s)")
    output_parts.append("=" * 80)

    return "\n".join(output_parts)


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


def format_runs_with_messages(
    runs: List[Dict[str, Any]], format_type: str = "pretty"
) -> Dict[str, Any]:
    """
    Format runs by extracting and formatting messages from each run.

    Args:
        runs: List of run dictionaries
        format_type: Output format ('raw', 'json', or 'pretty')

    Returns:
        Dictionary with formatted output based on format_type
    """
    all_messages = []

    # Extract messages from all runs
    for run in runs:
        run_messages = extract_messages_from_run(run)
        if run_messages:
            all_messages.extend(run_messages)

    # Format based on type
    if format_type == "raw":
        return {"messages": all_messages, "formatted": _format_raw(all_messages)}
    elif format_type == "json":
        return {"messages": all_messages, "formatted": _format_json(all_messages)}
    elif format_type == "pretty":
        return {"messages": all_messages, "formatted": _format_pretty(all_messages)}
    else:
        raise ValueError(f"Unknown format type: {format_type}")
