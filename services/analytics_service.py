from __future__ import annotations

from collections import defaultdict
from datetime import date as date_type
from datetime import timedelta

from config.settings import ProductivitySettings
from models.analytics import ProductivityMetrics
from models.commit import Commit

# A gap longer than this between two commits is treated as the end of a coding session.
_SESSION_GAP = timedelta(minutes=60)
# A session made of a single commit has no gap data to measure; assume this much focused time.
_SINGLE_COMMIT_ESTIMATE = timedelta(minutes=15)

# Rough "solid day" targets used to normalize the productivity score onto a 0-100 scale.
_TARGET_COMMITS = 8
_TARGET_LINES_CHANGED = 400
_TARGET_FILES_MODIFIED = 15
_TARGET_ACTIVE_HOURS = 6.0


class ProductivityAnalyticsService:
    """Module 5: pure, deterministic productivity metrics derived from a day's commits."""

    def __init__(self, settings: ProductivitySettings):
        self._settings = settings

    def compute(self, target_date: date_type, commits: list[Commit]) -> ProductivityMetrics:
        if not commits:
            return ProductivityMetrics(date=target_date)

        ordered = sorted(commits, key=lambda c: c.commit_time)
        lines_added = sum(c.insertions for c in ordered)
        lines_removed = sum(c.deletions for c in ordered)
        unique_files = {f.path for c in ordered for f in c.files_changed}
        total_lines_changed = lines_added + lines_removed

        sessions = self._group_into_sessions(ordered)
        durations = [self._session_duration(s) for s in sessions]
        longest_session = max(durations)
        active_time = sum(durations, timedelta())
        active_hours = active_time.total_seconds() / 3600

        score = self._productivity_score(
            num_commits=len(ordered),
            lines_changed=total_lines_changed,
            files_modified=len(unique_files),
            active_hours=active_hours,
        )

        return ProductivityMetrics(
            date=target_date,
            total_commits=len(ordered),
            files_modified=len(unique_files),
            lines_added=lines_added,
            lines_removed=lines_removed,
            most_edited_module=self._most_edited_module(ordered),
            longest_session_minutes=round(longest_session.total_seconds() / 60, 1),
            active_coding_hours=round(active_hours, 2),
            average_commit_size=round(total_lines_changed / len(ordered), 1),
            productivity_score=score,
        )

    @staticmethod
    def _group_into_sessions(ordered_commits: list[Commit]) -> list[list[Commit]]:
        sessions: list[list[Commit]] = [[ordered_commits[0]]]
        for commit in ordered_commits[1:]:
            if commit.commit_time - sessions[-1][-1].commit_time > _SESSION_GAP:
                sessions.append([commit])
            else:
                sessions[-1].append(commit)
        return sessions

    @staticmethod
    def _session_duration(session: list[Commit]) -> timedelta:
        if len(session) == 1:
            return _SINGLE_COMMIT_ESTIMATE
        return session[-1].commit_time - session[0].commit_time

    @staticmethod
    def _most_edited_module(commits: list[Commit]) -> str | None:
        counts: dict[str, int] = defaultdict(int)
        for commit in commits:
            for file in commit.files_changed:
                module = file.path.split("/")[0] if "/" in file.path else file.path
                counts[module] += file.insertions + file.deletions
        if not counts:
            return None
        return max(counts.items(), key=lambda kv: kv[1])[0]

    def _productivity_score(
        self, num_commits: int, lines_changed: int, files_modified: int, active_hours: float
    ) -> float:
        weights = self._settings.weights
        commit_component = min(num_commits / _TARGET_COMMITS, 1.0)
        lines_component = min(lines_changed / _TARGET_LINES_CHANGED, 1.0)
        files_component = min(files_modified / _TARGET_FILES_MODIFIED, 1.0)
        hours_component = min(active_hours / _TARGET_ACTIVE_HOURS, 1.0)

        score = (
            commit_component * weights.commits
            + lines_component * weights.lines_changed
            + files_component * weights.files_modified
            + hours_component * weights.active_hours
        )
        return round(score * 100, 1)
