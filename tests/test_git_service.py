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
