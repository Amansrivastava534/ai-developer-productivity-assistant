from __future__ import annotations

from models.commit import Commit


def format_commits_for_prompt(commits: list[Commit]) -> str:
    lines = []
    for c in commits:
        files = ", ".join(f.path for f in c.files_changed) or "no files recorded"
        lines.append(
            f"- [{c.short_hash}] ({c.repo_name}/{c.branch}) {c.commit_time.strftime('%H:%M')} "
            f"+{c.insertions}/-{c.deletions}: {c.message.strip()} | files: {files}"
        )
    return "\n".join(lines)
