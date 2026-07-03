from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class OllamaSettings(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:7b"
    timeout_seconds: int = 120


class GitSettings(BaseModel):
    repositories: list[Path] = Field(default_factory=list)
    author_email: str | None = None


class DatabaseSettings(BaseModel):
    path: Path = Path("database/assistant.db")

    @property
    def resolved_path(self) -> Path:
        return self.path if self.path.is_absolute() else PROJECT_ROOT / self.path


class ReportsSettings(BaseModel):
    output_dir: Path = Path("reports")

    @property
    def resolved_dir(self) -> Path:
        return self.output_dir if self.output_dir.is_absolute() else PROJECT_ROOT / self.output_dir


class LoggingSettings(BaseModel):
    level: str = "INFO"
    file: Path = Path("logs/assistant.log")

    @property
    def resolved_file(self) -> Path:
        return self.file if self.file.is_absolute() else PROJECT_ROOT / self.file


class ProductivityWeights(BaseModel):
    commits: float = 0.25
    lines_changed: float = 0.25
    files_modified: float = 0.2
    active_hours: float = 0.3


class ProductivitySettings(BaseModel):
    weights: ProductivityWeights = Field(default_factory=ProductivityWeights)


class Settings(BaseModel):
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    git: GitSettings = Field(default_factory=GitSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    reports: ReportsSettings = Field(default_factory=ReportsSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    productivity: ProductivitySettings = Field(default_factory=ProductivitySettings)

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Settings":
        load_dotenv(PROJECT_ROOT / ".env", override=False)
        config_path = config_path or Path(
            os.environ.get("DEV_ASSISTANT_CONFIG", PROJECT_ROOT / "config" / "config.yaml")
        )
        raw: dict = {}
        if config_path.exists():
            raw = yaml.safe_load(config_path.read_text()) or {}

        settings = cls.model_validate(raw)

        # Environment overrides, kept minimal: just enough to swap models/hosts without editing yaml.
        if env_model := os.environ.get("OLLAMA_MODEL"):
            settings.ollama.model = env_model
        if env_base_url := os.environ.get("OLLAMA_BASE_URL"):
            settings.ollama.base_url = env_base_url

        return settings


@lru_cache
def get_settings() -> Settings:
    return Settings.load()
