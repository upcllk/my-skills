#!/usr/bin/env python3
"""Read-only inventory of Label Studio task result sources."""

from __future__ import annotations

import argparse
import json
from collections import Counter

from label_studio_client import LabelStudioClient, LabelStudioError


def count(task: dict, field: str) -> int:
    value = task.get(field, [])
    return len(value) if isinstance(value, list) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", required=True, type=int)
    parser.add_argument("--json", action="store_true", help="emit complete task inventory as JSON")
    args = parser.parse_args()
    try:
        client = LabelStudioClient()
        project, tasks = client.project(args.project_id), client.tasks(args.project_id)
    except LabelStudioError as error:
        parser.error(str(error))
    rows = [{
        "task_id": task.get("id"), "current_annotation_count": count(task, "annotations"),
        "prediction_count": count(task, "predictions"), "draft_count": count(task, "drafts"),
        "is_labeled": task.get("is_labeled"), "draft_exists": task.get("draft_exists"), "state": task.get("state"),
    } for task in tasks]
    sources = Counter()
    for row in rows:
        for source, field in (("annotation", "current_annotation_count"), ("prediction", "prediction_count"), ("draft", "draft_count")):
            if row[field]: sources[source] += 1
    if args.json:
        print(json.dumps({"project": project, "tasks": rows}, ensure_ascii=False, indent=2))
        return 0
    print(f"Project: {project.get('title', project.get('id', args.project_id))}")
    print(f"Project ID: {args.project_id}\nTotal tasks: {len(rows)}")
    print("Tasks containing source: " + ", ".join(f"{key}={sources[key]}" for key in ("annotation", "prediction", "draft")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
