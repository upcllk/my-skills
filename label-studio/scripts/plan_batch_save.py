#!/usr/bin/env python3
"""Read-only conservative batch-save plan; it never writes to Label Studio."""

from __future__ import annotations

import argparse
import json
from collections import Counter

from label_studio_client import LabelStudioClient, LabelStudioError
from validation import validate


def count(task: dict, field: str) -> int:
    value = task.get(field, [])
    return len(value) if isinstance(value, list) else 0


def classify(task: dict) -> dict:
    annotations, predictions, drafts = (count(task, key) for key in ("annotations", "predictions", "drafts"))
    base = {"task_id": task.get("id"), "current_annotation_count": annotations, "prediction_count": predictions, "draft_count": drafts}
    if annotations and not drafts:
        return base | {"selected_result_source": "annotation", "planned_action": "Skip", "reason": "A durable annotation is present. Predictions alone do not evidence a pending human edit."}
    if not annotations and not predictions and not drafts:
        return base | {"selected_result_source": "unknown", "planned_action": "Skip", "reason": "No result source is present."}
    present = ", ".join(source for source, value in (("annotation", annotations), ("prediction", predictions), ("draft", drafts)) if value)
    return base | {"selected_result_source": "unknown", "planned_action": "Ambiguous", "reason": f"Unverified candidate source(s): {present}. No automatic save is safe."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", required=True, type=int)
    parser.add_argument("--dry-run", action="store_true", required=True, help="required guard; this script is read-only")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        client = LabelStudioClient()
        project, tasks = client.project(args.project_id), client.tasks(args.project_id)
    except LabelStudioError as error:
        parser.error(str(error))
    rows = [classify(task) for task in tasks]
    integrity = validate(tasks)
    actions = Counter(row["planned_action"] for row in rows)
    sources = Counter(row["selected_result_source"] for row in rows)
    payload = {"project": {"id": args.project_id, "title": project.get("title")}, "total_tasks": len(rows), "planned_actions": actions, "result_sources": sources, "integrity_findings": integrity["findings"], "tasks": rows}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=dict))
        return 0
    print("=" * 50)
    print("Label Studio Batch Annotation (dry run)")
    print("=" * 50)
    print(f"Project: {project.get('title', args.project_id)}")
    print(f"Project ID: {args.project_id}\nTotal tasks: {len(rows)}")
    print("Planned actions: " + ", ".join(f"{name}: {actions[name]}" for name in ("Submit", "Update", "Skip", "Ambiguous")))
    print("Result source: " + ", ".join(f"{name}: {sources[name]}" for name in ("prediction", "draft", "annotation", "unknown")))
    blocked = actions["Ambiguous"] + len(integrity["findings"])
    if blocked:
        print(f"BLOCKED: {actions['Ambiguous']} ambiguous source(s), {len(integrity['findings'])} integrity finding(s). No batch write may start.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
