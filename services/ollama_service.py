from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from config.settings import OllamaSettings

logger = logging.getLogger(__name__)


class OllamaUnavailableError(RuntimeError):
    """Raised when the local Ollama server cannot be reached or errors out."""


class OllamaService:
    """Thin async wrapper around the local Ollama HTTP API (/api/generate)."""

    def __init__(self, settings: OllamaSettings):
        self._settings = settings

    async def generate(self, prompt: str, system: str | None = None, json_mode: bool = False) -> str:
        payload: dict[str, Any] = {
            "model": self._settings.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        if json_mode:
            payload["format"] = "json"

        async with httpx.AsyncClient(
            base_url=self._settings.base_url, timeout=self._settings.timeout_seconds
        ) as client:
            try:
                response = await client.post("/api/generate", json=payload)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                logger.error("Ollama request failed: %s", exc)
                raise OllamaUnavailableError(
                    f"Could not reach Ollama at {self._settings.base_url}: {exc}"
                ) from exc

        return response.json().get("response", "").strip()

    async def generate_json(self, prompt: str, system: str | None = None) -> dict[str, Any]:
        raw = await self.generate(prompt, system=system, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Ollama returned non-JSON output, ignoring. First 200 chars: %s", raw[:200])
            return {}
