"""
Char-based pagination for LangSmith runs.

Stateless: each request fetches all runs for the trace (up to a safe bound),
builds pages by character budget, and returns the requested page only.
No cursor, no offset, no server-side state. Optimized for LLM callers (simple integers).
"""

import json
from typing import Any, Dict, List

# Safe upper bound for runs per trace per request
MAX_RUNS_PER_TRACE = 500


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


def _page_output_size(page_dict: Dict[str, Any], indent: int = 2) -> int:
    """Character count of the full page JSON (same format as when saving to file)."""
    # Use default ensure_ascii=True so size matches json.dump(..., indent=2) to file
    return len(json.dumps(page_dict, default=str, indent=indent))


def _enforce_page_char_budget(
    page_dict: Dict[str, Any],
    max_chars_per_page: int,
    *,
    indent: int = 2,
) -> Dict[str, Any]:
    """
    If the page JSON exceeds max_chars_per_page, truncate long strings inside
    page_dict["runs"] (in the middle of text) until the serialized output fits.
    Uses the same indent as the output format so saved files respect the budget.
    If still over budget after string truncation, the serialized JSON is cut
    in the middle and a truncation notice is appended (output is then invalid
    JSON but strictly under the character limit).
    Returns a new dict; does not mutate the input.
    """
    if _page_output_size(page_dict, indent) <= max_chars_per_page:
        return page_dict

    runs = page_dict.get("runs", [])
    if not runs:
        return page_dict

    # Binary search for max_string_len so that truncating all strings in runs
    # to that length yields a page output <= max_chars_per_page.
    low, high = 0, 100_000
    best_page_dict = page_dict

    while low <= high:
        mid = (low + high) // 2
        truncated_runs = [_truncate_strings(r, mid) for r in runs]
        test_dict = {**page_dict, "runs": truncated_runs}
        size = _page_output_size(test_dict, indent)

        if size <= max_chars_per_page:
            best_page_dict = test_dict
            low = mid + 1
        else:
            high = mid - 1

    # If still over (e.g. huge nested structure with few long strings), return a
    # valid dict with runs=[] and a truncated preview string so total output fits.
    best_size = _page_output_size(best_page_dict, indent)
    if best_size > max_chars_per_page:
        json_str = json.dumps(best_page_dict, default=str, indent=indent)
        suffix = "\n… (output truncated, exceeded max_chars_per_page)"
        # Reserve space for wrapper; long string may expand when JSON-escaped
        overhead = 1000
        safe_preview_len = (max_chars_per_page - len(suffix) - overhead) // 2
        preview_max = max(100, safe_preview_len)
        truncated_preview = json_str[:preview_max] + suffix
        return {
            "runs": [],
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
    Split runs into pages by character budget (JSON UTF-8 length).
    If a single run exceeds the budget, it is returned alone on a page.
    """
    if not runs_dict:
        return []

    pages: List[List[Dict[str, Any]]] = []
    current_page: List[Dict[str, Any]] = []
    current_chars = 0

    for run in runs_dict:
        run_chars = _run_char_count(run)
        # Start new page if adding this run would exceed budget and we already have items
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
    - Builds pages by accumulating JSON UTF-8 length up to max_chars_per_page.
    - page_number is 1-based. Out-of-range returns empty runs.

    Returns:
        {
            "runs": [...],
            "page_number": 1,
            "total_pages": N,
            "max_chars_per_page": int,
            "preview_chars": int,
        }
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


def paginate_runs_all_pages(
    runs_dict: List[Dict[str, Any]],
    max_chars_per_page: int,
    preview_chars: int = 0,
) -> List[Dict[str, Any]]:
    """
    Return a list of page dicts (one per page), each with the same shape as paginate_runs().
    Useful for saving or returning every page.
    """
    if preview_chars > 0:
        runs_dict = [_truncate_strings(r, preview_chars) for r in runs_dict]

    pages = build_pages_by_char_budget(runs_dict, max_chars_per_page)
    total_pages = len(pages)

    result = []
    for i, page in enumerate(pages):
        out = {
            "runs": page,
            "page_number": i + 1,
            "total_pages": total_pages,
            "max_chars_per_page": max_chars_per_page,
            "preview_chars": preview_chars,
        }
        result.append(_enforce_page_char_budget(out, max_chars_per_page))
    return result
