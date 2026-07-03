from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_type

from container import Container
from models.analysis import CodeChangeClassification, CommitGroup
from models.analytics import ProductivityMetrics
from models.commit import Commit
from models.summary import DailySummary


@dataclass
class DailyPipelineResult:
    date: date_type
    commits: list[Commit]
    groups: list[CommitGroup]
    classifications: list[CodeChangeClassification]
    human_summary: str
    technical_summary: str
    business_summary: str
    daily_summary: DailySummary
    metrics: ProductivityMetrics


async def run_daily_pipeline(container: Container, target_date: date_type) -> DailyPipelineResult:
    """Runs Modules 1-5 end to end for a single day and persists every result."""
    commits = container.git_analyzer.get_commits_for_date(target_date)
    container.commit_repo.save_commits(commits)

    groups = await container.commit_grouping.group(commits)
    container.commit_group_repo.save_groups(target_date, groups)

    classifications = await container.code_change.classify(commits)
    container.code_change_repo.save_classifications(target_date, classifications)

    human_summary, technical_summary, business_summary = await container.git_summary.summarize(commits)

    daily_summary = await container.daily_summary.generate(target_date, commits, groups)
    container.daily_summary_repo.upsert(daily_summary)

    metrics = container.analytics.compute(target_date, commits)
    container.productivity_repo.upsert(metrics)

    return DailyPipelineResult(
        date=target_date,
        commits=commits,
        groups=groups,
        classifications=classifications,
        human_summary=human_summary,
        technical_summary=technical_summary,
        business_summary=business_summary,
        daily_summary=daily_summary,
        metrics=metrics,
    )
