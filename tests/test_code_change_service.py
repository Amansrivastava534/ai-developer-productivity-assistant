from __future__ import annotations

from datetime import datetime

import pytest

from models.analysis import ChangeType
from models.commit import Commit, FileChange
from services.code_change_service import CodeChangeService


def _commit(message: str, *files: FileChange) -> Commit:
    return Commit(
        commit_hash="abc123",
        repo_name="demo",
        branch="main",
        author_name="Dev",
        author_email="dev@example.com",
        message=message,
        commit_time=datetime(2026, 7, 3, 9, 0),
        files_changed=list(files),
        insertions=sum(f.insertions for f in files),
        deletions=sum(f.deletions for f in files),
    )


@pytest.mark.asyncio
async def test_classifies_test_files_as_testing_without_calling_ollama():
    commit = _commit("add tests", FileChange(path="tests/test_foo.py", insertions=10, deletions=0))
    service = CodeChangeService(ollama=None)  # heuristics resolve this file, ollama is never touched
    result = await service.classify([commit])

    assert len(result) == 1
    assert result[0].change_type == ChangeType.TESTING
    assert result[0].confidence >= 0.8


@pytest.mark.asyncio
async def test_classifies_dependency_docs_and_config_files():
    commit = _commit(
        "chore: bump deps and docs",
        FileChange(path="requirements.txt", insertions=1, deletions=1),
        FileChange(path="README.md", insertions=3, deletions=0),
        FileChange(path="config/settings.yaml", insertions=2, deletions=0),
    )
    service = CodeChangeService(ollama=None)
    result = await service.classify([commit])

    by_path = {r.file_path: r.change_type for r in result}
    assert by_path["requirements.txt"] == ChangeType.DEPENDENCY_UPDATE
    assert by_path["README.md"] == ChangeType.DOCUMENTATION
    assert by_path["config/settings.yaml"] == ChangeType.CONFIGURATION


@pytest.mark.asyncio
async def test_pubspec_files_are_dependency_update_not_testing():
    # Regression test: "pubspec" contains the substring "spec", which a naive
    # substring match against test markers used to misclassify as Testing.
    commit = _commit(
        "chore: add google_mobile_ads dependency",
        FileChange(path="pubspec.yaml", insertions=5, deletions=0),
        FileChange(path="pubspec.lock", insertions=20, deletions=0),
    )
    service = CodeChangeService(ollama=None)
    result = await service.classify([commit])

    by_path = {r.file_path: r.change_type for r in result}
    assert by_path["pubspec.yaml"] == ChangeType.DEPENDENCY_UPDATE
    assert by_path["pubspec.lock"] == ChangeType.DEPENDENCY_UPDATE


@pytest.mark.asyncio
async def test_real_test_files_still_classified_as_testing():
    commit = _commit(
        "test: add widget tests",
        FileChange(path="test/widget_test.dart", insertions=15, deletions=0),
        FileChange(path="lib/foo.test.js", insertions=10, deletions=0),
        FileChange(path="lib/bar_test.go", insertions=8, deletions=0),
    )
    service = CodeChangeService(ollama=None)
    result = await service.classify([commit])

    by_path = {r.file_path: r.change_type for r in result}
    assert by_path["test/widget_test.dart"] == ChangeType.TESTING
    assert by_path["lib/foo.test.js"] == ChangeType.TESTING
    assert by_path["lib/bar_test.go"] == ChangeType.TESTING
