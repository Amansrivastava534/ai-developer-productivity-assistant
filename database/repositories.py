from __future__ import annotations

import json
from datetime import date as date_type
from datetime import datetime

from database.db import Database
from models.analysis import ChangeType, CodeChangeClassification, CommitGroup
from models.analytics import ProductivityMetrics
from models.commit import Commit, FileChange
from models.summary import DailySummary


class CommitRepository:
    def __init__(self, db: Database):
        self._db = db

    def save_commits(self, commits: list[Commit]) -> None:
        with self._db.connection() as conn:
            for commit in commits:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO commits
                        (commit_hash, repo_name, branch, author_name, author_email,
                         message, commit_time, commit_date, files_changed, insertions, deletions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        commit.commit_hash,
                        commit.repo_name,
                        commit.branch,
                        commit.author_name,
                        commit.author_email,
                        commit.message,
                        commit.commit_time.isoformat(),
                        commit.commit_time.date().isoformat(),
                        json.dumps([f.model_dump() for f in commit.files_changed]),
                        commit.insertions,
                        commit.deletions,
                    ),
                )

    def get_commits_for_date(self, date: date_type) -> list[Commit]:
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM commits WHERE commit_date = ? ORDER BY commit_time",
                (date.isoformat(),),
            ).fetchall()
        return [self._row_to_commit(row) for row in rows]

    @staticmethod
    def _row_to_commit(row) -> Commit:
        return Commit(
            commit_hash=row["commit_hash"],
            repo_name=row["repo_name"],
            branch=row["branch"],
            author_name=row["author_name"],
            author_email=row["author_email"],
            message=row["message"],
            commit_time=datetime.fromisoformat(row["commit_time"]),
            files_changed=[FileChange(**f) for f in json.loads(row["files_changed"])],
            insertions=row["insertions"],
            deletions=row["deletions"],
        )


class CommitGroupRepository:
    def __init__(self, db: Database):
        self._db = db

    def save_groups(self, date: date_type, groups: list[CommitGroup]) -> None:
        with self._db.connection() as conn:
            conn.execute("DELETE FROM commit_groups WHERE date = ?", (date.isoformat(),))
            for group in groups:
                conn.execute(
                    "INSERT INTO commit_groups (date, theme, commit_hashes, narrative) VALUES (?, ?, ?, ?)",
                    (date.isoformat(), group.theme, json.dumps(group.commit_hashes), group.narrative),
                )

    def get_groups_for_date(self, date: date_type) -> list[CommitGroup]:
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT theme, commit_hashes, narrative FROM commit_groups WHERE date = ?",
                (date.isoformat(),),
            ).fetchall()
        return [
            CommitGroup(theme=row["theme"], commit_hashes=json.loads(row["commit_hashes"]), narrative=row["narrative"])
            for row in rows
        ]


class CodeChangeRepository:
    def __init__(self, db: Database):
        self._db = db

    def save_classifications(self, date: date_type, classifications: list[CodeChangeClassification]) -> None:
        with self._db.connection() as conn:
            conn.execute("DELETE FROM code_changes WHERE date = ?", (date.isoformat(),))
            for c in classifications:
                conn.execute(
                    """
                    INSERT INTO code_changes (date, commit_hash, file_path, change_type, confidence, rationale)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (date.isoformat(), c.commit_hash, c.file_path, c.change_type.value, c.confidence, c.rationale),
                )

    def get_classifications_for_date(self, date: date_type) -> list[CodeChangeClassification]:
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT commit_hash, file_path, change_type, confidence, rationale FROM code_changes WHERE date = ?",
                (date.isoformat(),),
            ).fetchall()
        return [
            CodeChangeClassification(
                commit_hash=row["commit_hash"],
                file_path=row["file_path"],
                change_type=ChangeType(row["change_type"]),
                confidence=row["confidence"],
                rationale=row["rationale"] or "",
            )
            for row in rows
        ]


class DailySummaryRepository:
    def __init__(self, db: Database):
        self._db = db

    def upsert(self, summary: DailySummary) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO daily_summaries
                    (date, completed_work, major_accomplishments, challenges, code_reviews, blockers, tomorrow_plan, risk_items)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    completed_work = excluded.completed_work,
                    major_accomplishments = excluded.major_accomplishments,
                    challenges = excluded.challenges,
                    code_reviews = excluded.code_reviews,
                    blockers = excluded.blockers,
                    tomorrow_plan = excluded.tomorrow_plan,
                    risk_items = excluded.risk_items
                """,
                (
                    summary.date.isoformat(),
                    summary.completed_work,
                    summary.major_accomplishments,
                    summary.challenges,
                    summary.code_reviews,
                    summary.blockers,
                    summary.tomorrow_plan,
                    summary.risk_items,
                ),
            )

    def get_by_date(self, date: date_type) -> DailySummary | None:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM daily_summaries WHERE date = ?", (date.isoformat(),)
            ).fetchone()
        if row is None:
            return None
        return DailySummary(
            date=date,
            completed_work=row["completed_work"] or "",
            major_accomplishments=row["major_accomplishments"] or "",
            challenges=row["challenges"] or "",
            code_reviews=row["code_reviews"] or "",
            blockers=row["blockers"] or "",
            tomorrow_plan=row["tomorrow_plan"] or "",
            risk_items=row["risk_items"] or "",
        )


class ProductivityMetricsRepository:
    def __init__(self, db: Database):
        self._db = db

    def upsert(self, metrics: ProductivityMetrics) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO productivity_metrics
                    (date, total_commits, files_modified, lines_added, lines_removed,
                     most_edited_module, longest_session_minutes, active_coding_hours,
                     average_commit_size, productivity_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    total_commits = excluded.total_commits,
                    files_modified = excluded.files_modified,
                    lines_added = excluded.lines_added,
                    lines_removed = excluded.lines_removed,
                    most_edited_module = excluded.most_edited_module,
                    longest_session_minutes = excluded.longest_session_minutes,
                    active_coding_hours = excluded.active_coding_hours,
                    average_commit_size = excluded.average_commit_size,
                    productivity_score = excluded.productivity_score
                """,
                (
                    metrics.date.isoformat(),
                    metrics.total_commits,
                    metrics.files_modified,
                    metrics.lines_added,
                    metrics.lines_removed,
                    metrics.most_edited_module,
                    metrics.longest_session_minutes,
                    metrics.active_coding_hours,
                    metrics.average_commit_size,
                    metrics.productivity_score,
                ),
            )

    def get_by_date(self, date: date_type) -> ProductivityMetrics | None:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM productivity_metrics WHERE date = ?", (date.isoformat(),)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_metrics(row, date)

    def get_range(self, start: date_type, end: date_type) -> list[ProductivityMetrics]:
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM productivity_metrics WHERE date BETWEEN ? AND ? ORDER BY date",
                (start.isoformat(), end.isoformat()),
            ).fetchall()
        return [self._row_to_metrics(row, date_type.fromisoformat(row["date"])) for row in rows]

    @staticmethod
    def _row_to_metrics(row, date: date_type) -> ProductivityMetrics:
        return ProductivityMetrics(
            date=date,
            total_commits=row["total_commits"],
            files_modified=row["files_modified"],
            lines_added=row["lines_added"],
            lines_removed=row["lines_removed"],
            most_edited_module=row["most_edited_module"],
            longest_session_minutes=row["longest_session_minutes"],
            active_coding_hours=row["active_coding_hours"],
            average_commit_size=row["average_commit_size"],
            productivity_score=row["productivity_score"],
        )
