#!/usr/bin/env python3
"""Create, verify, and delete a disposable project to prove Submit/Update API semantics."""

from __future__ import annotations

from datetime import datetime, timezone

from label_studio_client import LabelStudioClient, LabelStudioError


CONFIG = """<View><Text name=\"text\" value=\"$text\"/><Choices name=\"choice\" toName=\"text\"><Choice value=\"first\"/><Choice value=\"second\"/></Choices></View>"""


def result(choice: str) -> list[dict]:
    return [{"from_name": "choice", "to_name": "text", "type": "choices", "value": {"choices": [choice]}}]


def main() -> int:
    client = LabelStudioClient()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    project_id: int | None = None
    try:
        project = client.post("/api/projects/", {"title": f"[Codex API verify {stamp}]", "label_config": CONFIG})
        project_id = int(project["id"])
        task = client.post("/api/tasks/", {"project": project_id, "data": {"text": "temporary API contract test"}})
        annotation = client.post(f"/api/tasks/{task['id']}/annotations/", {"result": result("first")})
        updated = client.patch(f"/api/annotations/{annotation['id']}/", {"result": result("second")})
        observed = updated.get("result") if isinstance(updated, dict) else None
        if observed != result("second"):
            raise LabelStudioError("PATCH response did not contain the replacement annotation result.")
        fetched = client.get(f"/api/annotations/{annotation['id']}/")
        if fetched.get("result") != result("second"):
            raise LabelStudioError("GET after PATCH did not preserve the updated result.")
        print(f"PASS: POST created annotation {annotation['id']}; PATCH persisted its replacement result.")
        return 0
    finally:
        if project_id is not None:
            client.delete(f"/api/projects/{project_id}/")
            print(f"CLEANUP: deleted temporary project {project_id}.")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LabelStudioError as error:
        raise SystemExit(f"FAIL: {error}")
