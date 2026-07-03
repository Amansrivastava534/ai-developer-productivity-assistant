from __future__ import annotations

from datetime import date as date_type

from pydantic import BaseModel

from models.commit import Commit


class DailyGitActivity(BaseModel):
    date: date_type
    commits: list[Commit] = []
    human_summary: str = ""
    technical_summary: str = ""
    business_summary: str = ""


class DailySummary(BaseModel):
    date: date_type
    completed_work: str = ""
    major_accomplishments: str = ""
    challenges: str = ""
    code_reviews: str = ""
    blockers: str = ""
    tomorrow_plan: str = ""
    risk_items: str = ""
