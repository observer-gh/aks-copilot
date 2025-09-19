# Dev Handoff — Story 2.2: AI-Powered Patching (Suggestion Review & Merge)

Status: READY FOR DEV  
Priority: High  
Predecessor: Story 2.1 (LLM Integration Foundation) ✅  
Objective: Convert LLM-driven suggestions into reviewable, validated patch candidates that can be selectively merged into `patch.json` while preserving safety guarantees.

---

## Problem & Goal

We now have LLM explanation & suggestion primitives. We need a controlled pathway to:

1. Generate patch suggestions for non-deterministic rules (e.g., SC003 Ingress class/TLS).
2. Validate & store them separately (e.g., `suggestions.json`).
3. Let a human (or future policy) approve which suggestions merge into the main patch set.
4. Ensure invalid / unsafe ops are never merged.

---

## Scope (In)

- Suggestion generation for SC003 (Ingress): propose adding `ingressClassName` or TLS stanza if absent.
- Suggestion storage format (`suggestions.json`).
- Merge CLI command to incorporate approved suggestions into `patch.json` (append new envelopes or merge ops into existing resource envelopes).
- Validation enhancements: reject ops targeting forbidden paths (e.g. metadata.uid, status, annotations.\* that aren't whitelisted).
- Logging of suggestion lifecycle: generated → (approved|rejected) → merged.

## Scope (Out)

- Automatic acceptance logic (policy engine) — future story.
- Real cluster live diff/hydration before merging.
- Multi-provider ranking or scoring of suggestions.

---

## Artifacts & Files

Add / Edit:

- `src/llm/augment.py` (extend) — function: `generate_resource_suggestions(violations)` batching calls.
- `src/patch/suggestions.py` (new) — persistence helpers:
  - `write_suggestions(suggestions: List[dict], path: str = "suggestions.json")`
  - `load_suggestions(path: str) -> List[dict]`
  - `filter_approved(all_suggestions, approved_ids_or_indices)`
- `src/patch/validator.py` (extend) — strengthen `_validate_patch_ops(ops)` + add `_is_forbidden_path(path)`.
- `src/cli/main.py` — new commands:
  - `suggest` — generate LLM suggestions from a violations file (only for rules flagged suggestible, e.g., SC003) → write `suggestions.json`.
  - `merge-suggestions` — read `suggestions.json` plus `--approve <list>` (comma-separated indices or IDs) and output merged `patch.json` (create or extend existing).
- Tests:
  - `tests/test_suggestions_generation.py` — stub LLM to return valid/invalid suggestion; ensure invalid filtered.
  - `tests/test_suggestions_merge.py` — approve subset and verify patch merge correctness.
  - `tests/test_validator_forbidden_paths.py` — ensure forbidden paths rejected.
  - Extend existing CLI tests or add `tests/test_cli_suggest_merge.py`.

---

## Data Shapes

### Suggestion (raw LLM output expected/normalized)

```json
{
  "type": "patch_suggestion",
  "rule_id": "SC003",
  "resource": { "kind": "Ingress", "name": "web" },
  "ops": [{ "op": "add", "path": "/spec/ingressClassName", "value": "web" }],
  "explanation": "Adding ingressClassName improves portability"
}
```

### Stored suggestions file (`suggestions.json`)

Array of suggestion envelopes:

```json
[
  {
    "index": 0,
    "rule_id": "SC003",
    "file": "manifests/ingress.yml",
    "resource": {"kind": "Ingress", "name": "web"},
    "ops": [...],
    "explanation": "...",
    "valid": true,
    "rejected": false
  }
]
```

### Merge Result

Either modify existing `patch.json` or create one with added envelopes. If resource/file already present, append new ops unless path duplicate conflict; on duplicate path conflict, prefer new op only if not semantic duplicate (same op/path/value). Provide a conflict summary.

---

## CLI Additions

### `copilot suggest <violations.json> [--out suggestions.json] [--rule SC003]`

- Loads violations; filters by rule (default SC003) & those lacking deterministic patch.
- Calls `generate_suggestion` per violation.
- Validates each suggestion; marks invalid ones `valid=false` (excluded from merge) but still records them.
- Writes suggestions file with index numbers.

### `copilot merge-suggestions <suggestions.json> [--approve 0,2,5] [--patch patch.json]`

- Loads suggestions and existing patch file (if present).
- Filters to approved indices (or all valid if `--approve` missing but prompt optional warning).
- Validates ops again (defense in depth).
- Emits updated `patch.json` and summary:
  - total suggestions, approved, merged, skipped (invalid, duplicate, conflict).

Exit codes:

- 0 success
- 2 partial (some invalid/conflicts) — still writes patch
- > 2 fatal (I/O issues)

---

## Validation Rules (Additions)

- Forbidden path prefixes: `/metadata/uid`, `/metadata/creationTimestamp`, `/status`, `/metadata/managedFields`.
- Only allow `add`, `replace` ops.
- Value size guard: serialized op value length <= 8KB.
- Max ops per suggestion (e.g., <= 10) else reject.

---

## Acceptance Criteria

1. `copilot suggest` produces `suggestions.json` with at least one valid SC003 suggestion (using stubbed LLM in tests).
2. Invalid LLM JSON or forbidden paths result in `valid=false` suggestions, not merged.
3. `copilot merge-suggestions` merges only approved indices; patch operations appear in `patch.json` envelopes consistent with existing schema ("file", "resource", "ops").
4. Duplicate path ops in same resource collapse to one (last-wins or skip-duplicate; document choice in code docstring).
5. All new tests pass; existing tests unaffected.
6. Logging: suggestion events (generate, merge) logged via `log_llm` or a new `log_patch_event` (optional) with success/failure.

---

## Test Plan Summary

| Test                            | Purpose                                   |
| ------------------------------- | ----------------------------------------- |
| test_suggest_generates_valid    | Valid suggestion stored with `valid=true` |
| test_suggest_invalid_json       | Malformed suggestion -> `valid=false`     |
| test_suggest_forbidden_path     | Forbidden path op rejected                |
| test_merge_approves_subset      | Only specified indices merged             |
| test_merge_handles_duplicates   | Duplicate path resolution policy enforced |
| test_merge_conflict_reporting   | Conflicts reported & exit code 2          |
| test_cli_suggest_and_merge_flow | End-to-end generation + merge             |

---

## Implementation Steps (Checklist)

1. Add `src/patch/suggestions.py` (I/O + filtering + merge utilities).
2. Extend validator with forbidden path logic.
3. Implement `copilot suggest` command.
4. Implement `copilot merge-suggestions` command.
5. Write tests (unit then CLI integration).
6. Update docs (README / story references) if necessary.
7. Run full test suite & adjust.

---

## Risks & Mitigations

| Risk                          | Mitigation                                |
| ----------------------------- | ----------------------------------------- |
| LLM suggests unsafe path      | Forbidden path filter + validator         |
| Large suggestion file         | Cap ops & value sizes                     |
| Silent merge conflicts        | Conflict summary + non-zero exit (2)      |
| Performance (many violations) | Batch prompts later (future optimization) |

---

## Definition of Done

- New commands available and documented via `--help`.
- Suggestions workflow demonstrably separate from deterministic patch path.
- All tests green; no regression warnings beyond existing.

## Assignment Block (Copy/Paste)

Task: Story 2.2 — AI-powered patching (suggestion review & merge)  
Priority: High  
Deliverables: suggestion generation command, merge command, validator enhancements, tests, updated patch workflow.  
Exit Criteria: Acceptance criteria satisfied; tests green.  
Branch Name Suggestion: `feat/ai-patching-2-2`

---

If you need an abbreviated version for a ticket, let me know.
