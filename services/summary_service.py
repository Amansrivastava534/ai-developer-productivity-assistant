from __future__ import annotations

from datetime import date as date_type

from models.analysis import CommitGroup
from models.commit import Commit
from models.summary import DailySummary
from prompts.daily_summary import build_daily_summary_prompt
from services.ai_text import stringify_field
from services.ollama_service import OllamaService

_NO_COMMITS_NOTE = "No commits recorded today."
_UNAVAILABLE_NOTE = "Not available."


class DailySummaryService:
    """Module 4: generates the end-of-day AI status report."""

    def __init__(self, ollama: OllamaService):
        self._ollama = ollama

    async def generate(
        self, target_date: date_type, commits: list[Commit], groups: list[CommitGroup]
    ) -> DailySummary:
        if not commits:
            return DailySummary(
                date=target_date,
                completed_work=_NO_COMMITS_NOTE,
                major_accomplishments=_NO_COMMITS_NOTE,
                challenges=_NO_COMMITS_NOTE,
                code_reviews=_NO_COMMITS_NOTE,
                blockers=_NO_COMMITS_NOTE,
                tomorrow_plan=_NO_COMMITS_NOTE,
                risk_items=_NO_COMMITS_NOTE,
            )

        system, prompt = build_daily_summary_prompt(commits, groups)
        data = await self._ollama.generate_json(prompt, system=system)

        return DailySummary(
            date=target_date,
            completed_work=stringify_field(data.get("completed_work"), _UNAVAILABLE_NOTE),
            major_accomplishments=stringify_field(data.get("major_accomplishments"), _UNAVAILABLE_NOTE),
            challenges=stringify_field(data.get("challenges"), _UNAVAILABLE_NOTE),
            code_reviews=stringify_field(data.get("code_reviews"), _UNAVAILABLE_NOTE),
            blockers=stringify_field(data.get("blockers"), _UNAVAILABLE_NOTE),
            tomorrow_plan=stringify_field(data.get("tomorrow_plan"), _UNAVAILABLE_NOTE),
            risk_items=stringify_field(data.get("risk_items"), _UNAVAILABLE_NOTE),
        )
