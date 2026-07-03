from __future__ import annotations

from datetime import date, datetime

from config.settings import ProductivitySettings
from models.commit import Commit, FileChange
from services.analytics_service import ProductivityAnalyticsService


def _commit(hour: int, minute: int, insertions: int, deletions: int, files: list[str]) -> Commit:
    return Commit(
        commit_hash=f"hash-{hour}{minute}",
        repo_name="demo",
        branch="main",
        author_name="Dev",
        author_email="dev@example.com",
        message="did stuff",
        commit_time=datetime(2026, 7, 3, hour, minute),
        files_changed=[FileChange(path=f, insertions=insertions, deletions=deletions) for f in files],
        insertions=insertions * len(files),
        deletions=deletions * len(files),
    )


def test_compute_returns_zeroed_metrics_for_no_commits():
    service = ProductivityAnalyticsService(ProductivitySettings())
    metrics = service.compute(date(2026, 7, 3), [])
    assert metrics.total_commits == 0
    assert metrics.productivity_score == 0.0


def test_compute_aggregates_commits_correctly():
    commits = [
        _commit(9, 0, 10, 2, ["services/a.py"]),
        _commit(9, 30, 5, 1, ["services/a.py", "services/b.py"]),
        _commit(14, 0, 20, 0, ["ui/dashboard.py"]),
    ]
    service = ProductivityAnalyticsService(ProductivitySettings())
    metrics = service.compute(date(2026, 7, 3), commits)

    assert metrics.total_commits == 3
    assert metrics.files_modified == 3
    assert metrics.lines_added == 40
    assert metrics.lines_removed == 4
    assert metrics.most_edited_module == "services"


def test_session_grouping_splits_on_large_gaps():
    commits = [
        _commit(9, 0, 5, 0, ["a.py"]),
        _commit(9, 10, 5, 0, ["a.py"]),
        _commit(15, 0, 5, 0, ["b.py"]),
    ]
    service = ProductivityAnalyticsService(ProductivitySettings())
    metrics = service.compute(date(2026, 7, 3), commits)

    # session 1: 9:00-9:10 = 10 min; session 2: single commit -> 15 min estimate
    assert metrics.longest_session_minutes == 15.0
