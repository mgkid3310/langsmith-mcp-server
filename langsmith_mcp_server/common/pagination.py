"""
Char-based pagination for LangSmith runs.

Stateless: each request fetches all runs for the trace (up to a safe bound),
builds pages by character budget, and returns the requested page only.
No cursor, no offset, no server-side state. Optimized for LLM callers (simple integers).
"""

import json
from typing import Any, Dict, List

# LangSmith API maximum; do not exceed
MAX_RUNS_PER_TRACE = 100


def _truncate_strings(obj: Any, preview_chars: int) -> Any:
    """Recursively truncate long strings to preview_chars; suffix with '… (+N chars)'."""
    if preview_chars <= 0:
        return obj
    if isinstance(obj, str):
        if len(obj) <= preview_chars:
            return obj
        return obj[:preview_chars] + "… (+" + str(len(obj) - preview_chars) + " chars)"
    if isinstance(obj, dict):
        return {k: _truncate_strings(v, preview_chars) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_truncate_strings(item, preview_chars) for item in obj]
    if isinstance(obj, tuple):
        return tuple(_truncate_strings(item, preview_chars) for item in obj)
    return obj


def _run_char_count(run_dict: Dict[str, Any]) -> int:
    """Character count of JSON-serialized run (for budget)."""
    return len(json.dumps(run_dict, ensure_ascii=False, default=str))


def _page_output_size(page_dict: Dict[str, Any], indent: int = 0) -> int:
    """Character count of the full page JSON. Use indent=0 for compact (budget-friendly)."""
    return len(json.dumps(page_dict, default=str, indent=indent if indent else None))


def _enforce_page_char_budget(
    page_dict: Dict[str, Any],
    max_chars_per_page: int,
    *,
    indent: int = 0,
    items_key: str = "runs",
) -> Dict[str, Any]:
    """
    If the page JSON exceeds max_chars_per_page, truncate long strings inside
    page_dict[items_key] until the serialized output fits.
    If still over budget, return a dict with items_key=[] and _truncated_preview.
    """
    if _page_output_size(page_dict, indent) <= max_chars_per_page:
        return page_dict

    items = page_dict.get(items_key, [])
    if not items:
        return page_dict

    low, high = 0, 100_000
    best_page_dict = page_dict

    while low <= high:
        mid = (low + high) // 2
        truncated_items = [_truncate_strings(it, mid) for it in items]
        test_dict = {**page_dict, items_key: truncated_items}
        size = _page_output_size(test_dict, indent)

        if size <= max_chars_per_page:
            best_page_dict = test_dict
            low = mid + 1
        else:
            high = mid - 1

    best_size = _page_output_size(best_page_dict, indent)
    if best_size > max_chars_per_page:
        json_str = json.dumps(best_page_dict, default=str, indent=indent if indent else None)
        suffix = "\n… (output truncated, exceeded max_chars_per_page)"
        overhead = 1000
        safe_preview_len = (max_chars_per_page - len(suffix) - overhead) // 2
        preview_max = max(100, safe_preview_len)
        truncated_preview = json_str[:preview_max] + suffix
        return {
            **{k: v for k, v in page_dict.items() if k != items_key},
            items_key: [],
            "page_number": page_dict["page_number"],
            "total_pages": page_dict["total_pages"],
            "max_chars_per_page": max_chars_per_page,
            "preview_chars": page_dict.get("preview_chars", 0),
            "_truncated": True,
            "_truncated_message": "Page exceeded character budget; content truncated.",
            "_truncated_preview": truncated_preview,
        }
    return best_page_dict


def build_pages_by_char_budget(
    runs_dict: List[Dict[str, Any]],
    max_chars_per_page: int,
) -> List[List[Dict[str, Any]]]:
    """
    Split runs into pages by character budget (JSON length).
    If a single run exceeds the budget, it is returned alone on a page.
    """
    if not runs_dict:
        return []

    pages: List[List[Dict[str, Any]]] = []
    current_page: List[Dict[str, Any]] = []
    current_chars = 0

    for run in runs_dict:
        run_chars = _run_char_count(run)
        if current_chars + run_chars > max_chars_per_page and current_page:
            pages.append(current_page)
            current_page = []
            current_chars = 0
        current_page.append(run)
        current_chars += run_chars

    if current_page:
        pages.append(current_page)
    return pages


def paginate_runs(
    runs_dict: List[Dict[str, Any]],
    page_number: int,
    max_chars_per_page: int,
    preview_chars: int = 0,
) -> Dict[str, Any]:
    """
    Return one page of runs (char-based pagination).

    - Applies preview_chars truncation to each run if preview_chars > 0.
    - Builds pages by accumulating JSON length up to max_chars_per_page.
    - page_number is 1-based. Out-of-range returns empty runs.
    - Ensures the returned page JSON never exceeds max_chars_per_page (truncates in the middle of text if needed).

    Returns:
        Dict with keys: runs, page_number, total_pages, max_chars_per_page, preview_chars.
        May include _truncated, _truncated_message, _truncated_preview if content was cut.
    """
    if preview_chars > 0:
        runs_dict = [_truncate_strings(r, preview_chars) for r in runs_dict]

    pages = build_pages_by_char_budget(runs_dict, max_chars_per_page)
    total_pages = len(pages)

    if page_number < 1 or page_number > total_pages:
        page_runs: List[Dict[str, Any]] = []
    else:
        page_runs = pages[page_number - 1]

    out = {
        "runs": page_runs,
        "page_number": page_number,
        "total_pages": total_pages,
        "max_chars_per_page": max_chars_per_page,
        "preview_chars": preview_chars,
    }
    return _enforce_page_char_budget(out, max_chars_per_page)


def paginate_messages(
    messages_dict: List[Dict[str, Any]],
    page_number: int,
    max_chars_per_page: int,
    preview_chars: int = 0,
) -> Dict[str, Any]:
    """
    Return one page of messages (char-based pagination), same semantics as paginate_runs.
    Uses "result" as the key for the message list.
    """
    if preview_chars > 0:
        messages_dict = [_truncate_strings(m, preview_chars) for m in messages_dict]

    # Same char-count logic as runs (each message is a dict)
    pages = build_pages_by_char_budget(messages_dict, max_chars_per_page)
    total_pages = len(pages)

    if page_number < 1 or page_number > total_pages:
        page_messages: List[Dict[str, Any]] = []
    else:
        page_messages = pages[page_number - 1]

    out = {
        "result": page_messages,
        "page_number": page_number,
        "total_pages": total_pages,
        "max_chars_per_page": max_chars_per_page,
        "preview_chars": preview_chars,
    }
    return _enforce_page_char_budget(out, max_chars_per_page, items_key="result")
