#!/usr/bin/env python3
"""Validate required targets and point-group object-count consistency without writing."""

from __future__ import annotations

import argparse
import json

from label_studio_client import LabelStudioClient, LabelStudioError
from validation import validate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", required=True, type=int)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-issues", action="store_true", help="return exit code 2 when any blocking finding exists")
    args = parser.parse_args()
    try:
        client = LabelStudioClient()
        project, tasks = client.project(args.project_id), client.tasks(args.project_id)
    except LabelStudioError as error:
        parser.error(str(error))
    report = {"project": {"id": args.project_id, "title": project.get("title")}, **validate(tasks)}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Project: {project.get('title', args.project_id)}\nProject ID: {args.project_id}")
        print(f"Blocking findings: {len(report['findings'])}")
        for finding in report["findings"]:
            print(f"- task {finding['task_id']}: {finding['check']} — {finding['detail']}")
    return 2 if args.fail_on_issues and report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
