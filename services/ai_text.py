from __future__ import annotations

from typing import Any


def stringify_field(value: Any, default: str = "") -> str:
    """Normalizes an LLM JSON field to prose text.

    Small local models frequently return a list of bullet points instead of a
    single string even when explicitly asked for prose, so this coerces either
    shape into plain text instead of leaking a Python repr into reports.
    """
    if value is None:
        return default
    if isinstance(value, list):
        text = "\n".join(f"- {item}" for item in value)
    else:
        text = str(value)
    return text.strip() or default
