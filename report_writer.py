from __future__ import annotations

from pathlib import Path

from pipeline import DailyPipelineResult


def write_daily_report(result: DailyPipelineResult, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{result.date.isoformat()}.md"

    lines = [
        f"# Daily Report — {result.date.isoformat()}",
        "",
        "## Human Summary",
        result.human_summary,
        "",
        "## Technical Summary",
        result.technical_summary,
        "",
        "## Business Summary",
        result.business_summary,
        "",
        "## Commit Groups",
    ]
    lines += (
        [f"- **{g.theme}**: {g.narrative}" for g in result.groups] if result.groups else ["(none)"]
    )

    summary = result.daily_summary
    lines += [
        "",
        "## Daily Summary",
        f"**Completed Work**: {summary.completed_work}",
        f"**Major Accomplishments**: {summary.major_accomplishments}",
        f"**Challenges**: {summary.challenges}",
        f"**Code Reviews**: {summary.code_reviews}",
        f"**Blockers**: {summary.blockers}",
        f"**Tomorrow's Plan**: {summary.tomorrow_plan}",
        f"**Risk Items**: {summary.risk_items}",
        "",
        "## Productivity Analytics",
        f"- Commits: {result.metrics.total_commits}",
        f"- Files modified: {result.metrics.files_modified}",
        f"- Lines added / removed: +{result.metrics.lines_added} / -{result.metrics.lines_removed}",
        f"- Most edited module: {result.metrics.most_edited_module or 'N/A'}",
        f"- Longest session: {result.metrics.longest_session_minutes} min",
        f"- Active coding hours: {result.metrics.active_coding_hours}",
        f"- Average commit size: {result.metrics.average_commit_size} lines",
        f"- Productivity score: {result.metrics.productivity_score}/100",
        "",
        "## Code Change Breakdown",
    ]
    lines += (
        [f"- `{c.file_path}` -> {c.change_type.value} (confidence {c.confidence:.2f})" for c in result.classifications]
        if result.classifications
        else ["(none)"]
    )

    path.write_text("\n".join(lines) + "\n")
    return path
