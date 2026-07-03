from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FileChange(BaseModel):
    path: str
    insertions: int = 0
    deletions: int = 0
    change_type: str = "modified"  # added | modified | deleted | renamed


class Commit(BaseModel):
    commit_hash: str
    repo_name: str
    branch: str
    author_name: str
    author_email: str
    message: str
    commit_time: datetime
    files_changed: list[FileChange] = []
    insertions: int = 0
    deletions: int = 0

    @property
    def total_lines_changed(self) -> int:
        return self.insertions + self.deletions

    @property
    def short_hash(self) -> str:
        return self.commit_hash[:8]
