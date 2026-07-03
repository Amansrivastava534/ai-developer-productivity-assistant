from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from models.analytics import ProductivityMetrics
from models.summary import DailySummary
from pipeline import DailyPipelineResult

console = Console()


def render_dashboard(result: DailyPipelineResult) -> None:
    console.rule(f"[bold]Daily Dashboard — {result.date.isoformat()}[/bold]")
    console.print(Panel(result.human_summary, title="Today's Work"))

    table = Table(title="Commits")
    table.add_column("Time")
    table.add_column("Repo/Branch")
    table.add_column("Message")
    table.add_column("+/-")
    for c in result.commits:
        table.add_row(
            c.commit_time.strftime("%H:%M"),
            f"{c.repo_name}/{c.branch}",
            c.message.strip().splitlines()[0],
            f"+{c.insertions}/-{c.deletions}",
        )
    console.print(table)

    render_metrics(result.metrics)
    render_daily_summary(result.daily_summary)


def render_metrics(metrics: ProductivityMetrics) -> None:
    table = Table(title="Productivity Analytics")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Commits", str(metrics.total_commits))
    table.add_row("Files modified", str(metrics.files_modified))
    table.add_row("Lines added / removed", f"+{metrics.lines_added} / -{metrics.lines_removed}")
    table.add_row("Most edited module", metrics.most_edited_module or "N/A")
    table.add_row("Longest session (min)", str(metrics.longest_session_minutes))
    table.add_row("Active coding hours", str(metrics.active_coding_hours))
    table.add_row("Average commit size", str(metrics.average_commit_size))
    table.add_row("Productivity score", f"{metrics.productivity_score}/100")
    console.print(table)


def render_daily_summary(summary: DailySummary) -> None:
    body = (
        f"[bold]Completed Work[/bold]\n{summary.completed_work}\n\n"
        f"[bold]Major Accomplishments[/bold]\n{summary.major_accomplishments}\n\n"
        f"[bold]Challenges[/bold]\n{summary.challenges}\n\n"
        f"[bold]Code Reviews[/bold]\n{summary.code_reviews}\n\n"
        f"[bold]Blockers[/bold]\n{summary.blockers}\n\n"
        f"[bold]Tomorrow's Plan[/bold]\n{summary.tomorrow_plan}\n\n"
        f"[bold]Risk Items[/bold]\n{summary.risk_items}"
    )
    console.print(Panel(body, title="AI Daily Summary"))
