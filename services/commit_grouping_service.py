from __future__ import annotations

from models.analysis import CommitGroup
from models.commit import Commit
from prompts.commit_grouping import build_commit_grouping_prompt
from services.ollama_service import OllamaService


class CommitGroupingService:
    """Module 2: turns a flat list of commit messages into thematic, narrative groups."""

    def __init__(self, ollama: OllamaService):
        self._ollama = ollama

    async def group(self, commits: list[Commit]) -> list[CommitGroup]:
        if not commits:
            return []

        system, prompt = build_commit_grouping_prompt(commits)
        data = await self._ollama.generate_json(prompt, system=system)

        short_to_full = {c.short_hash: c.commit_hash for c in commits}
        groups: list[CommitGroup] = []
        for raw_group in data.get("groups", []):
            theme = str(raw_group.get("theme", "")).strip()
            narrative = str(raw_group.get("narrative", "")).strip()
            if not theme or not narrative:
                continue
            full_hashes = [
                short_to_full[h] for h in raw_group.get("commit_hashes", []) if h in short_to_full
            ]
            groups.append(CommitGroup(theme=theme, commit_hashes=full_hashes, narrative=narrative))

        if groups:
            return groups

        return [self._fallback_group(commits)]

    @staticmethod
    def _fallback_group(commits: list[Commit]) -> CommitGroup:
        messages = "; ".join(c.message.strip().splitlines()[0] for c in commits)
        return CommitGroup(
            theme="Today's Work",
            commit_hashes=[c.commit_hash for c in commits],
            narrative=f"Made {len(commits)} commit(s): {messages}",
        )
