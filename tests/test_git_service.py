from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from git import Repo

from config.settings import GitSettings
from services.git_service import GitActivityAnalyzer


@pytest.fixture
def repo_path(tmp_path: Path) -> Path:
    repo = Repo.init(tmp_path)
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test Dev")
        cw.set_value("user", "email", "dev@example.com")

    (tmp_path / "app.py").write_text("print('hello')\n")
    repo.index.add(["app.py"])
    repo.index.commit(
        "feat: add hello world",
        author_date="2026-07-03T09:00:00",
        commit_date="2026-07-03T09:00:00",
    )

    (tmp_path / "app.py").write_text("print('hello world')\n")
    repo.index.add(["app.py"])
    repo.index.commit(
        "fix: greet properly",
        author_date="2026-07-02T09:00:00",
        commit_date="2026-07-02T09:00:00",
    )
    return tmp_path


def test_get_commits_for_date_filters_by_day(repo_path: Path):
    analyzer = GitActivityAnalyzer(GitSettings(repositories=[repo_path]))
    commits = analyzer.get_commits_for_date(date(2026, 7, 3))

    assert len(commits) == 1
    assert commits[0].message.startswith("feat: add hello world")
    assert commits[0].repo_name == repo_path.name
    assert commits[0].insertions == 1
    assert commits[0].files_changed[0].path == "app.py"
    assert commits[0].files_changed[0].change_type == "added"


def test_get_commits_for_date_returns_empty_for_no_activity(repo_path: Path):
    analyzer = GitActivityAnalyzer(GitSettings(repositories=[repo_path]))
    commits = analyzer.get_commits_for_date(date(2020, 1, 1))
    assert commits == []


def test_get_commits_for_date_scans_all_local_branches_not_just_the_checked_out_one(
    tmp_path: Path,
):
    repo = Repo.init(tmp_path)
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test Dev")
        cw.set_value("user", "email", "dev@example.com")

    (tmp_path / "base.py").write_text("base\n")
    repo.index.add(["base.py"])
    repo.index.commit(
        "chore: initial commit",
        author_date="2026-07-01T09:00:00",
        commit_date="2026-07-01T09:00:00",
    )
    default_branch = repo.heads[0]

    branch_a = repo.create_head("feature-a")
    branch_a.checkout()
    (tmp_path / "a.py").write_text("a\n")
    repo.index.add(["a.py"])
    repo.index.commit(
        "feat: work on branch a",
        author_date="2026-07-03T09:00:00",
        commit_date="2026-07-03T09:00:00",
    )

    default_branch.checkout()
    branch_b = repo.create_head("feature-b")
    branch_b.checkout()
    (tmp_path / "b.py").write_text("b\n")
    repo.index.add(["b.py"])
    repo.index.commit(
        "feat: work on branch b",
        author_date="2026-07-03T10:00:00",
        commit_date="2026-07-03T10:00:00",
    )
    # feature-b is left as the checked-out branch, mimicking switching branches
    # after doing earlier work on feature-a.

    analyzer = GitActivityAnalyzer(GitSettings(repositories=[tmp_path]))
    commits = analyzer.get_commits_for_date(date(2026, 7, 3))

    messages = {c.message.strip() for c in commits}
    assert messages == {"feat: work on branch a", "feat: work on branch b"}
    branches = {c.branch for c in commits}
    assert branches == {"feature-a", "feature-b"}
