from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime

import typer

from container import build_container
from pipeline import run_daily_pipeline
from report_writer import write_daily_report
from ui.dashboard import render_dashboard, render_daily_summary, render_metrics

app = typer.Typer(help="AI Developer Productivity Assistant -- local, offline, powered by Ollama.")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _parse_date(value: str | None) -> date:
    if value is None:
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


@app.command()
def analyze(day: str = typer.Option(None, "--date", help="YYYY-MM-DD, defaults to today")) -> None:
    """Run the full Git Analyzer -> Grouping -> Code Change -> Summary -> Analytics pipeline."""
    target_date = _parse_date(day)
    container = build_container()
    result = asyncio.run(run_daily_pipeline(container, target_date))
    report_path = write_daily_report(result, container.settings.reports.resolved_dir)
    typer.echo(f"Analyzed {len(result.commits)} commit(s) for {target_date}. Report: {report_path}")
    render_dashboard(result)


@app.command()
def summary(day: str = typer.Option(None, "--date", help="YYYY-MM-DD, defaults to today")) -> None:
    """Show the AI daily summary for a day, computing it if it hasn't been generated yet."""
    target_date = _parse_date(day)
    container = build_container()
    cached = container.daily_summary_repo.get_by_date(target_date)
    if cached is None:
        result = asyncio.run(run_daily_pipeline(container, target_date))
        cached = result.daily_summary
    render_daily_summary(cached)


@app.command()
def analytics(day: str = typer.Option(None, "--date", help="YYYY-MM-DD, defaults to today")) -> None:
    """Show productivity analytics for a day, computing them if not already cached."""
    target_date = _parse_date(day)
    container = build_container()
    cached = container.productivity_repo.get_by_date(target_date)
    if cached is None:
        commits = container.git_analyzer.get_commits_for_date(target_date)
        container.commit_repo.save_commits(commits)
        cached = container.analytics.compute(target_date, commits)
        container.productivity_repo.upsert(cached)
    render_metrics(cached)


@app.command()
def dashboard(day: str = typer.Option(None, "--date", help="YYYY-MM-DD, defaults to today")) -> None:
    """Render the full Rich console dashboard for a day (runs the pipeline first)."""
    target_date = _parse_date(day)
    container = build_container()
    result = asyncio.run(run_daily_pipeline(container, target_date))
    render_dashboard(result)


if __name__ == "__main__":
    app()
