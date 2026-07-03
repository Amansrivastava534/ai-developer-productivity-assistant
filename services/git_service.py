from __future__ import annotations

import logging
from datetime import date as date_type
from datetime import datetime
from pathlib import Path

from git import NULL_TREE, Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError

from config.settings import GitSettings
from models.commit import Commit, FileChange
from prompts.git_summary import build_git_activity_prompt
from services.ai_text import stringify_field
from services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

_CHANGE_TYPE_MAP = {"A": "added", "D": "deleted", "M": "modified", "R": "renamed", "C": "added"}


class GitActivityAnalyzer:
    """Module 1: reads local git repositories and extracts a given day's commits."""

    def __init__(self, settings: GitSettings):
        self._settings = settings

    def get_commits_for_date(self, target_date: date_type) -> list[Commit]:
        commits: list[Commit] = []
        for repo_path in self._settings.repositories:
            commits.extend(self._commits_from_repo(Path(repo_path), target_date))
        commits.sort(key=lambda c: c.commit_time)
        return commits

    def _commits_from_repo(self, repo_path: Path, target_date: date_type) -> list[Commit]:
        try:
            repo = Repo(repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            logger.warning("Skipping %s: not a usable git repository (%s)", repo_path, exc)
            return []

        if repo.bare or not repo.head.is_valid():
            return []

        author_email = self._settings.author_email or self._repo_user_email(repo)
        branch = self._current_branch(repo)
        repo_name = repo_path.name

        # Deliberately not using git's --since/--until: their revision walk assumes commit
        # dates increase monotonically while walking the graph and can silently skip commits
        # after a rebase, cherry-pick, or backdated commit. A full scan is the correct one.
        results: list[Commit] = []
        for git_commit in repo.iter_commits(branch):
            commit_dt = git_commit.committed_datetime
            if commit_dt.date() != target_date:
                continue
            if author_email and git_commit.author.email != author_email:
                continue

            results.append(self._to_commit(git_commit, repo_name, branch, commit_dt))
        return results

    def _to_commit(self, git_commit, repo_name: str, branch: str, commit_dt: datetime) -> Commit:
        stats = git_commit.stats
        change_types = self._file_change_types(git_commit)
        files_changed = [
            FileChange(
                path=path,
                insertions=file_stats["insertions"],
                deletions=file_stats["deletions"],
                change_type=change_types.get(path, "modified"),
            )
            for path, file_stats in stats.files.items()
        ]
        return Commit(
            commit_hash=git_commit.hexsha,
            repo_name=repo_name,
            branch=branch,
            author_name=git_commit.author.name or "unknown",
            author_email=git_commit.author.email or "unknown",
            message=git_commit.message.strip(),
            commit_time=commit_dt,
            files_changed=files_changed,
            insertions=stats.total.get("insertions", 0),
            deletions=stats.total.get("deletions", 0),
        )

    @staticmethod
    def _file_change_types(git_commit) -> dict[str, str]:
        result: dict[str, str] = {}
        try:
            if git_commit.parents:
                diffs = git_commit.parents[0].diff(git_commit)
            else:
                diffs = git_commit.diff(NULL_TREE)
            for diff in diffs:
                path = diff.b_path or diff.a_path
                if path:
                    result[path] = _CHANGE_TYPE_MAP.get(diff.change_type, "modified")
        except Exception as exc:  # pragma: no cover - diff computation is best-effort metadata
            logger.debug("Could not compute per-file change types for %s: %s", git_commit.hexsha, exc)
        return result

    @staticmethod
    def _current_branch(repo: Repo) -> str:
        try:
            return repo.active_branch.name
        except TypeError:
            return "detached-head"

    @staticmethod
    def _repo_user_email(repo: Repo) -> str | None:
        try:
            return repo.config_reader().get_value("user", "email")
        except Exception:
            return None


class GitSummaryGenerator:
    """Module 1: turns a day's raw commits into human/technical/business summaries via Ollama."""

    def __init__(self, ollama: OllamaService):
        self._ollama = ollama

    async def summarize(self, commits: list[Commit]) -> tuple[str, str, str]:
        if not commits:
            empty = "No commits recorded today."
            return empty, empty, empty

        system, prompt = build_git_activity_prompt(commits)
        data = await self._ollama.generate_json(prompt, system=system)
        fallback = "Summary unavailable."
        return (
            stringify_field(data.get("human_summary"), fallback),
            stringify_field(data.get("technical_summary"), fallback),
            stringify_field(data.get("business_summary"), fallback),
        )
