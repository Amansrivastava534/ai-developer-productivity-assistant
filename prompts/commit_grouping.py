from __future__ import annotations

from models.commit import Commit

SYSTEM_PROMPT = (
    "You are an engineering assistant that groups a developer's commit messages into "
    "coherent themes and writes one narrative sentence per theme, in the style of a "
    "release note. Do not invent details that aren't implied by the commit messages."
)


def build_commit_grouping_prompt(commits: list[Commit]) -> tuple[str, str]:
    commit_lines = "\n".join(
        f"- [{c.short_hash}] {c.message.strip().splitlines()[0]}" for c in commits
    )
    prompt = f"""Group these commit messages into 1-5 coherent themes \
(e.g. authentication, API integration, UI improvements, bug fixes, performance):

{commit_lines}

Respond with a JSON object of the form:
{{"groups": [{{"theme": "short theme name", "commit_hashes": ["<short hash>", ...], \
"narrative": "one sentence describing what was accomplished for this theme"}}]}}

Every commit hash must appear in exactly one group. Respond with only the JSON object."""
    return SYSTEM_PROMPT, prompt
