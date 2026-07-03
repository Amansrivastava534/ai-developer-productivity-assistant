from __future__ import annotations

from models.commit import Commit
from prompts.formatting import format_commits_for_prompt

SYSTEM_PROMPT = (
    "You are an engineering assistant that reads a developer's raw git commit history "
    "for a single day and writes concise, accurate summaries. Only use facts present in "
    "the commit list; never invent work that isn't there. Respond with strict JSON only."
)


def build_git_activity_prompt(commits: list[Commit]) -> tuple[str, str]:
    commit_text = format_commits_for_prompt(commits)
    prompt = f"""Here are today's git commits:

{commit_text}

Write three summaries of this work as a JSON object with exactly these keys:
- "human_summary": a plain-English, friendly recap a teammate could read in Slack (2-4 sentences).
- "technical_summary": an engineer-facing recap naming the specific modules/files/mechanisms touched (2-5 sentences).
- "business_summary": a non-technical recap framed around user/business impact, no jargon (2-3 sentences).

Respond with only the JSON object, no markdown fences, no extra commentary."""
    return SYSTEM_PROMPT, prompt
