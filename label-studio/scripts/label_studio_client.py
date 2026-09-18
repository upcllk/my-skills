#!/usr/bin/env python3
"""Small read-only Label Studio client used by the bundled inspection scripts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class LabelStudioError(RuntimeError):
    pass


def load_skill_env() -> None:
    """Load simple KEY=VALUE entries from the skill-local .env without logging them."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


class LabelStudioClient:
    def __init__(self, url: str | None = None, api_key: str | None = None) -> None:
        load_skill_env()
        self.url = (url or os.environ.get("LABEL_STUDIO_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("LABEL_STUDIO_API_KEY", "")
        if not self.url or not self.api_key:
            raise LabelStudioError(
                "Set LABEL_STUDIO_URL and LABEL_STUDIO_API_KEY before accessing Label Studio."
            )

    def request(self, method: str, path: str, query: dict[str, Any] | None = None, payload: Any | None = None) -> Any:
        suffix = f"?{urlencode(query)}" if query else ""
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.url}{path}{suffix}",
            headers={"Authorization": f"Token {self.api_key}", "Accept": "application/json", "Content-Type": "application/json"},
            data=body,
            method=method,
        )
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:500]
            raise LabelStudioError(f"{method} {path} failed with HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise LabelStudioError(f"Could not reach Label Studio at {self.url}: {error.reason}") from error

    def get(self, path: str, query: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, query=query)

    def post(self, path: str, payload: Any) -> Any:
        return self.request("POST", path, payload=payload)

    def patch(self, path: str, payload: Any) -> Any:
        return self.request("PATCH", path, payload=payload)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)

    def project(self, project_id: int) -> dict[str, Any]:
        payload = self.get(f"/api/projects/{project_id}")
        if not isinstance(payload, dict):
            raise LabelStudioError("Unexpected project response shape.")
        return payload

    def tasks(self, project_id: int) -> list[dict[str, Any]]:
        """List all tasks, accommodating common paginated and list response shapes."""
        tasks: list[dict[str, Any]] = []
        page = 1
        page_size = 100
        while True:
            payload = self.get(f"/api/projects/{project_id}/tasks/", {"page": page, "page_size": page_size})
            if isinstance(payload, list):
                batch, next_page = payload, len(payload) == page_size
            elif isinstance(payload, dict):
                batch = payload.get("tasks") or payload.get("results") or []
                next_page = bool(payload.get("next"))
            else:
                raise LabelStudioError("Unexpected task-list response shape.")
            if not isinstance(batch, list):
                raise LabelStudioError("Task list did not contain an array.")
            tasks.extend(item for item in batch if isinstance(item, dict))
            if not next_page or not batch:
                return tasks
            page += 1
