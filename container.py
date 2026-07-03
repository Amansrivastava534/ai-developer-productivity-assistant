from __future__ import annotations

from dataclasses import dataclass

from config.settings import Settings, get_settings
from database.db import Database
from database.repositories import (
    CodeChangeRepository,
    CommitGroupRepository,
    CommitRepository,
    DailySummaryRepository,
    ProductivityMetricsRepository,
)
from services.analytics_service import ProductivityAnalyticsService
from services.code_change_service import CodeChangeService
from services.commit_grouping_service import CommitGroupingService
from services.git_service import GitActivityAnalyzer, GitSummaryGenerator
from services.ollama_service import OllamaService
from services.summary_service import DailySummaryService


@dataclass
class Container:
    """Composition root: wires config, storage, and services together (dependency injection)."""

    settings: Settings
    db: Database
    ollama: OllamaService
    git_analyzer: GitActivityAnalyzer
    git_summary: GitSummaryGenerator
    commit_grouping: CommitGroupingService
    code_change: CodeChangeService
    daily_summary: DailySummaryService
    analytics: ProductivityAnalyticsService
    commit_repo: CommitRepository
    commit_group_repo: CommitGroupRepository
    code_change_repo: CodeChangeRepository
    daily_summary_repo: DailySummaryRepository
    productivity_repo: ProductivityMetricsRepository


def build_container(settings: Settings | None = None) -> Container:
    settings = settings or get_settings()
    db = Database(settings.database.resolved_path)
    ollama = OllamaService(settings.ollama)

    return Container(
        settings=settings,
        db=db,
        ollama=ollama,
        git_analyzer=GitActivityAnalyzer(settings.git),
        git_summary=GitSummaryGenerator(ollama),
        commit_grouping=CommitGroupingService(ollama),
        code_change=CodeChangeService(ollama),
        daily_summary=DailySummaryService(ollama),
        analytics=ProductivityAnalyticsService(settings.productivity),
        commit_repo=CommitRepository(db),
        commit_group_repo=CommitGroupRepository(db),
        code_change_repo=CodeChangeRepository(db),
        daily_summary_repo=DailySummaryRepository(db),
        productivity_repo=ProductivityMetricsRepository(db),
    )
