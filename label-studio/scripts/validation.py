"""Read-only integrity checks for Label Studio object-detection annotations."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def latest_annotation(task: dict[str, Any]) -> dict[str, Any] | None:
    annotations = [item for item in task.get("annotations", []) if isinstance(item, dict)]
    if not annotations:
        return None
    return max(annotations, key=lambda item: (str(item.get("updated_at", "")), str(item.get("created_at", "")), item.get("id", 0)))


def rectangle_labels(annotation: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for result in annotation.get("result", []):
        if not isinstance(result, dict):
            continue
        value = result.get("value", {})
        if not isinstance(value, dict):
            continue
        for key, names in value.items():
            if key.endswith("labels") and isinstance(names, list):
                labels.extend(str(name) for name in names)
    return labels


def rectangle_count(annotation: dict[str, Any]) -> int:
    return sum(
        1
        for result in annotation.get("result", [])
        if isinstance(result, dict)
        and isinstance(result.get("value"), dict)
        and any(key.endswith("labels") and value for key, value in result["value"].items())
    )


def point_group(task: dict[str, Any]) -> str:
    data = task.get("data", {})
    if not isinstance(data, dict):
        return "unknown"
    explicit = data.get("camera_point_group")
    if explicit:
        return str(explicit)
    camera, point = data.get("camera", "unknown-camera"), data.get("point", "unknown-point")
    return f"{camera}｜点位 {point}"


def validate(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Return blocking task-level integrity findings and point-group baselines."""
    findings: list[dict[str, Any]] = []
    counts_by_group: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for task in tasks:
        task_id = task.get("id")
        annotation = latest_annotation(task)
        if annotation is None:
            findings.append({"task_id": task_id, "check": "missing_annotation", "detail": "No durable annotation exists."})
            continue
        result_count = rectangle_count(annotation)
        if not result_count:
            findings.append({"task_id": task_id, "check": "empty_annotation", "detail": "Latest annotation contains no labeled object region."})
        expected = task.get("data", {}).get("core_target_labels", []) if isinstance(task.get("data"), dict) else []
        expected = {str(label) for label in expected if label}
        observed = set(rectangle_labels(annotation))
        missing = sorted(expected - observed)
        if missing:
            findings.append({"task_id": task_id, "check": "missing_core_target", "detail": "Missing required core label(s): " + ", ".join(missing)})
        counts_by_group[point_group(task)].append((int(task_id) if task_id is not None else -1, result_count))

    baselines: dict[str, dict[str, Any]] = {}
    for group, members in counts_by_group.items():
        if len(members) < 2:
            continue
        frequencies = Counter(count for _, count in members)
        expected_count = max(frequencies, key=lambda count: (frequencies[count], count))
        baselines[group] = {"tasks": len(members), "expected_rectangle_count": expected_count}
        for task_id, count in members:
            if count != expected_count:
                findings.append({"task_id": task_id, "check": "rectangle_count_outlier", "detail": f"Point group {group!r} normally has {expected_count} labeled regions; this task has {count}."})
    return {"findings": findings, "point_group_baselines": baselines}
