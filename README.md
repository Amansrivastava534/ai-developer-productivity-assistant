# AI Developer Productivity Assistant

A local-first, offline AI engineering-manager assistant. It reads your git commit
history for a day, understands it with a local Ollama model, and produces
human/technical/business summaries, a daily status report, and productivity
analytics — no cloud APIs involved.

This is the **core MVP slice**: a production-quality architecture skeleton
(config, SQLite storage, an async Ollama client, dependency-injected services)
plus five fully working modules:

1. **Git Activity Analyzer** — extracts a day's commits (message, branch, files,
   insertions/deletions, repo, time) from local repos and writes human/technical/
   business summaries.
2. **Smart Commit Grouping** — turns a flat list of commit messages into
   thematic, narrative groups (e.g. "Resolved multiple issues related to
   authentication, API integration, and UI improvements").
3. **Code Change Understanding** — classifies each changed file as New Feature,
   Bug Fix, Refactoring, Optimization, Testing, Documentation, Configuration, or
   Dependency Update, with a confidence score. Obvious cases (test dirs, lockfiles,
   docs, config extensions) are resolved with fast local heuristics; everything
   else is classified by the model.
4. **AI Daily Summary** — Completed Work / Major Accomplishments / Challenges /
   Code Reviews / Blockers / Tomorrow's Plan / Risk Items.
5. **Productivity Analytics** — commits, files modified, lines added/removed,
   most-edited module, longest coding session, active coding hours, average
   commit size, and a weighted productivity score. Pure computation, no AI.

Everything else in the original spec (release notes, PR descriptions, Jira,
meeting notes, Flutter/Realm tooling, JSON inspector, chat mode, semantic
search, knowledge base, full dashboard) is intentionally out of scope for this
slice — the architecture below (services + repositories + DI container) is
built so each of those can be added as one more service without touching the
rest of the system.

## Architecture

```
developer_assistant/
├── config/          # config.yaml + pydantic-validated settings loader
├── models/          # Pydantic domain models (Commit, DailySummary, ...)
├── database/         # SQLite schema + repository classes (one per table)
├── services/         # One class per module, constructor-injected dependencies
├── prompts/          # Prompt builders, kept separate from service logic
├── cli/               # Typer CLI (composition root wires everything together)
├── api/               # Thin FastAPI shell exposing the same services over HTTP
├── ui/                # Rich console dashboard
├── reports/           # Generated markdown reports land here
├── logs/              # Log output
├── tests/             # pytest unit tests
├── container.py        # Dependency-injection composition root
├── pipeline.py          # Orchestrates Modules 1-5 into one daily run
└── report_writer.py      # Renders a DailyPipelineResult to markdown
```

Every service takes its dependencies (an `OllamaService`, a `Database`, settings
objects) through its constructor rather than reaching for globals, so each one
can be tested and swapped independently.

## Setup

### 1. Install and start Ollama

```bash
brew install ollama
brew services start ollama
ollama pull llama3.2          # or qwen2.5-coder:7b, deepseek-coder, mistral, codellama
```

### 2. Configure

`config/config.yaml` is gitignored (it holds your local repo paths, which can
be sensitive) — create your own from the template and edit it:

```bash
cp config/config.example.yaml config/config.yaml
```

```yaml
ollama:
  base_url: "http://localhost:11434"
  model: "llama3.2:latest"    # must match a model you've pulled
git:
  repositories:
    - /path/to/your/repo-1
    - /path/to/your/repo-2
  author_email: null          # null = use each repo's `git config user.email`
```

`OLLAMA_MODEL` and `OLLAMA_BASE_URL` environment variables (via `.env`) override
the yaml if set.

### 3. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run

All commands must be run from this directory (`developer_assistant/`) so
Python can resolve the package-style imports.

```bash
# Full pipeline for today (or --date YYYY-MM-DD), writes reports/<date>.md
python -m cli.main analyze

# Just the AI daily summary (computes it if not cached yet)
python -m cli.main summary --date 2026-04-13

# Just productivity analytics
python -m cli.main analytics --date 2026-04-13

# Full Rich dashboard
python -m cli.main dashboard --date 2026-04-13

# Or via the FastAPI shell
python -m uvicorn api.main:app --reload
# POST /api/analyze?day=YYYY-MM-DD, GET /api/summary?day=..., GET /api/analytics?day=...
```

### 5. Test

```bash
python -m pytest
```

## Data

All results are persisted to a local SQLite database at
`database/assistant.db` (commits, commit groups, code-change classifications,
daily summaries, productivity metrics), so `summary`/`analytics` commands
reuse a day's results instead of recomputing them.

## Extending

Each of the remaining modules from the original spec (release notes, PR
descriptions, Jira linking, meeting notes, Flutter log analysis, Realm query
generation, JSON inspection, daily email, weekly reports, AI chat, semantic
search, knowledge base, full dashboard) fits the same shape: a service class
in `services/`, a prompt builder in `prompts/` if it talks to Ollama, a
repository in `database/` if it needs persistence, and a new `cli/main.py`
command or `api/main.py` route to expose it.
