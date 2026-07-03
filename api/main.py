from __future__ import annotations

from datetime import date, datetime

from fastapi import FastAPI, HTTPException

from container import build_container
from models.analytics import ProductivityMetrics
from models.summary import DailySummary
from pipeline import run_daily_pipeline

app = FastAPI(
    title="AI Developer Productivity Assistant",
    description="Local-first developer activity insights, powered by Ollama.",
    version="0.1.0",
)


def _parse_date(value: str | None) -> date:
    if value is None:
        return date.today()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="date must be formatted as YYYY-MM-DD") from exc


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(day: str | None = None) -> dict:
    """Runs the full Modules 1-5 pipeline for the given day (defaults to today)."""
    target_date = _parse_date(day)
    container = build_container()
    result = await run_daily_pipeline(container, target_date)
    return {
        "date": result.date.isoformat(),
        "commit_count": len(result.commits),
        "human_summary": result.human_summary,
        "technical_summary": result.technical_summary,
        "business_summary": result.business_summary,
        "daily_summary": result.daily_summary.model_dump(),
        "metrics": result.metrics.model_dump(),
    }


@app.get("/api/summary", response_model=DailySummary)
def get_summary(day: str | None = None) -> DailySummary:
    container = build_container()
    target_date = _parse_date(day)
    cached = container.daily_summary_repo.get_by_date(target_date)
    if cached is None:
        raise HTTPException(status_code=404, detail="No summary generated for this date yet")
    return cached


@app.get("/api/analytics", response_model=ProductivityMetrics)
def get_analytics(day: str | None = None) -> ProductivityMetrics:
    container = build_container()
    target_date = _parse_date(day)
    cached = container.productivity_repo.get_by_date(target_date)
    if cached is None:
        raise HTTPException(status_code=404, detail="No analytics generated for this date yet")
    return cached
