CREATE TABLE IF NOT EXISTS commits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commit_hash TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    branch TEXT NOT NULL,
    author_name TEXT NOT NULL,
    author_email TEXT NOT NULL,
    message TEXT NOT NULL,
    commit_time TEXT NOT NULL,
    commit_date TEXT NOT NULL,
    files_changed TEXT NOT NULL DEFAULT '[]',
    insertions INTEGER NOT NULL DEFAULT 0,
    deletions INTEGER NOT NULL DEFAULT 0,
    UNIQUE(commit_hash, repo_name)
);

CREATE INDEX IF NOT EXISTS idx_commits_date ON commits(commit_date);

CREATE TABLE IF NOT EXISTS commit_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    theme TEXT NOT NULL,
    commit_hashes TEXT NOT NULL DEFAULT '[]',
    narrative TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_commit_groups_date ON commit_groups(date);

CREATE TABLE IF NOT EXISTS code_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    commit_hash TEXT NOT NULL,
    file_path TEXT NOT NULL,
    change_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    rationale TEXT
);

CREATE INDEX IF NOT EXISTS idx_code_changes_date ON code_changes(date);

CREATE TABLE IF NOT EXISTS daily_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    completed_work TEXT,
    major_accomplishments TEXT,
    challenges TEXT,
    code_reviews TEXT,
    blockers TEXT,
    tomorrow_plan TEXT,
    risk_items TEXT
);

CREATE TABLE IF NOT EXISTS productivity_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    total_commits INTEGER NOT NULL DEFAULT 0,
    files_modified INTEGER NOT NULL DEFAULT 0,
    lines_added INTEGER NOT NULL DEFAULT 0,
    lines_removed INTEGER NOT NULL DEFAULT 0,
    most_edited_module TEXT,
    longest_session_minutes REAL NOT NULL DEFAULT 0,
    active_coding_hours REAL NOT NULL DEFAULT 0,
    average_commit_size REAL NOT NULL DEFAULT 0,
    productivity_score REAL NOT NULL DEFAULT 0
);
