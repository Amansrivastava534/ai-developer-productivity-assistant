from __future__ import annotations

from models.analysis import CommitGroup
from models.commit import Commit
from prompts.formatting import format_commits_for_prompt

SYSTEM_PROMPT = (
    "You are an AI engineering-manager assistant writing an end-of-day status report for a "
    "software engineer, based only on their day's git activity. Be concrete and specific, "
    "grounded in the commits given. If a section has no evidence (e.g. no blockers), say so "
    "plainly rather than inventing content."
)


def build_daily_summary_prompt(commits: list[Commit], groups: list[CommitGroup]) -> tuple[str, str]:
    commit_text = format_commits_for_prompt(commits)
    group_text = "\n".join(f"- {g.theme}: {g.narrative}" for g in groups) or "(none)"
    prompt = f"""Today's commits:
{commit_text}

Thematic groups:
{group_text}

Write a daily status report as a JSON object with exactly these keys (short prose or bullet \
points as plain text, 1-4 sentences each):
- "completed_work"
- "major_accomplishments"
- "challenges"
- "code_reviews"
- "blockers"
- "tomorrow_plan"
- "risk_items"

Base everything only on the commit evidence above. For code_reviews, blockers, tomorrow_plan, \
and risk_items, if there is no direct evidence in the commits, write \
"None noted from today's commits." rather than fabricating specifics.
Respond with only the JSON object."""
    return SYSTEM_PROMPT, prompt
