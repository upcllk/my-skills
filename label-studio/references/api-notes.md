# Label Studio API notes

Source: the Label Studio OpenAPI specification, retrieved 2026-09-12 from `https://api.labelstud.io/openapi.json`. Confirm the local server's supported behavior before writing.

## Relevant resource shapes

The task schema includes `annotations`, `predictions`, and `drafts`, plus useful state fields such as `is_labeled`, `draft_exists`, `updated_at`, `completed_at`, and `submission`.

An annotation creation request accepts a `result` and task/project-related metadata. An existing annotation can be updated using the annotation PATCH endpoint. These are durable annotation operations; they do not automatically establish that a prediction or draft is reviewer-approved.

## Relevant endpoints

| Purpose | Endpoint | Method |
| --- | --- | --- |
| List task annotations | `/api/tasks/{id}/annotations/` | GET |
| Create annotation (Submit equivalent) | `/api/tasks/{id}/annotations/` | POST |
| Read an annotation | `/api/annotations/{id}/` | GET |
| Update annotation (Update equivalent) | `/api/annotations/{id}/` | PATCH |
| Bulk annotation API | `/api/annotations/bulk/` | POST |

Do not use a bulk endpoint as a shortcut around source selection, backups, or per-task outcome tracking.

## Source-selection rule

Use a prediction only when a project-specific workflow has positively recorded it as approved. Use a draft only after verifying that it contains the front-end's intended saved result for the local version. If an annotation, draft, and prediction disagree or their relationship cannot be proven, classify the task as `Ambiguous`.

## Local 1.23.0 verification

On 2026-09-12, a disposable project/task was used to verify the local server. Creating an annotation with POST and replacing its result with PATCH both persisted as expected. In the browser, selecting a label without clicking Submit left the task API response at `annotations: []`, `predictions: []`, `drafts: null`. Therefore those unsaved UI edits are browser-only state and cannot be collected by a later API batch operation. The disposable projects were deleted after testing.
