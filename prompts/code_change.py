from __future__ import annotations

from models.commit import Commit, FileChange

SYSTEM_PROMPT = (
    "You are an engineering assistant that classifies individual file changes from a git "
    "commit into exactly one category: New Feature, Bug Fix, Refactoring, Optimization, "
    "Testing, Documentation, Configuration, Dependency Update. Base your judgment only on "
    "the commit message and file path/line-change counts given; when unsure, lower the "
    "confidence score rather than guessing."
)


def build_code_change_prompt(items: list[tuple[Commit, FileChange]]) -> tuple[str, str]:
    lines = "\n".join(
        f'{i}. commit message: "{commit.message.strip().splitlines()[0]}" | '
        f"file: `{file.path}` | change: {file.change_type} +{file.insertions}/-{file.deletions}"
        for i, (commit, file) in enumerate(items)
    )
    prompt = f"""Classify each of these file changes:

{lines}

Respond with a JSON object of the form:
{{"classifications": [{{"index": 0, "change_type": "New Feature", "confidence": 0.0, "rationale": "short reason"}}, ...]}}

change_type must be exactly one of: New Feature, Bug Fix, Refactoring, Optimization, Testing, \
Documentation, Configuration, Dependency Update.
Include one entry per index above. Respond with only the JSON object."""
    return SYSTEM_PROMPT, prompt
