from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    NEW_FEATURE = "New Feature"
    BUG_FIX = "Bug Fix"
    REFACTORING = "Refactoring"
    OPTIMIZATION = "Optimization"
    TESTING = "Testing"
    DOCUMENTATION = "Documentation"
    CONFIGURATION = "Configuration"
    DEPENDENCY_UPDATE = "Dependency Update"


class CodeChangeClassification(BaseModel):
    file_path: str
    commit_hash: str
    change_type: ChangeType
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class CommitGroup(BaseModel):
    theme: str
    commit_hashes: list[str]
    narrative: str
