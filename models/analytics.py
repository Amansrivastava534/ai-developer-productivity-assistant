from __future__ import annotations

from datetime import date as date_type

from pydantic import BaseModel


class ProductivityMetrics(BaseModel):
    date: date_type
    total_commits: int = 0
    files_modified: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    most_edited_module: str | None = None
    longest_session_minutes: float = 0.0
    active_coding_hours: float = 0.0
    average_commit_size: float = 0.0
    productivity_score: float = 0.0
