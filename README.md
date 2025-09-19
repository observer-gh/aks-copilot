# AKS Copilot (MVP)

Migration helper for moving k3s-style Kubernetes manifests toward AKS conventions. Provides:

- Static inspection rules (SC001 storageClass, SC002 resource requests/limits, SC003 ingress best‑practices)
- Report + deterministic patch generation for safe rules
- (Story 2.2) AI / heuristic powered patch SUGGESTION workflow with explicit human approval gate

Status: Experimental MVP, safe-by-default (LLM optional, disabled = deterministic heuristics only for SC003).

---

## Quick Start

```
uv run python -m src.cli.main validate examples/enemy/deploy.yml
uv run python -m src.cli.main fix examples/enemy/deploy.yml
```

## AI Suggestion Workflow (Story 2.2)

Two-stage process: generate suggestions → selectively merge into a patch.

1. Prepare a `violations.json` array (each item: id/rule_id, file, kind, name, path, etc.). The existing inspection pipeline can be extended to emit this.
2. Run `suggest` to create `suggestions.json` (schema wrapped). Example:
   ```
   uv run python -m src.cli.main suggest violations.json --rule SC003
   ```
3. Inspect `suggestions.json` (see schema below). Decide which indices to approve.
4. Merge approved suggestions into (or create) `patch.json`:
   ```
   uv run python -m src.cli.main merge-suggestions suggestions.json --approve 0,2 --patch patch.json
   ```
   Omitting `--approve` auto‑approves all VALID suggestions (implicit approve‑all). Consider using explicit indices in CI.
5. Apply downstream (future: dry-run + live apply).

## Exit Codes

- `suggest` – 0 on success, non‑zero on IO / parse error.
- `merge-suggestions` – 0 if merged cleanly (no conflicts, no invalid requested indices). 2 if conflicts OR any requested indices were invalid/missing. Non‑zero (1) for usage / file errors.

## Verbose Conflict Details

Use `--verbose` with `merge-suggestions` to list each conflicting path showing previous vs new value:

```
CONFLICT file=ing.yml path=/spec/ingressClassName previous="oldclass" new="newclass"
```

Conflicts still merge (last op appended); exit code signals reviewer attention (2).

## Suggestions Schema

File `suggestions.json` (schema_version=1):

```json
{
  "schema_version": 1,
  "generated_at": "2025-09-19T12:00:00Z",
  "rule": "SC003",
  "meta": { "total": 3, "valid": 2 },
  "suggestions": [
    {
      "index": 0,
      "rule_id": "SC003",
      "file": "ing.yml",
      "resource": { "kind": "Ingress", "name": "web" },
      "ops": [
        { "op": "add", "path": "/spec/ingressClassName", "value": "web" }
      ],
      "explanation": "…optional LLM text…",
      "valid": true,
      "reason": "",
      "rejected": false
    }
  ]
}
```

Legacy flat list (array only) still loads (backward compatible reader).

## Validation / Guardrails

- Op whitelist: `add`, `replace`.
- Forbidden path prefixes: `/metadata/uid`, `/metadata/creationTimestamp`, `/metadata/managedFields`, `/status`.
- Per suggestion op cap: 10; global merge validation via `validate_patch_ops`.
- Value size guard (8 KB serialized) (implemented in validator code—see `src/patch/validator.py`).
- Dry‑run phases (for earlier deterministic patch commands) ensure JSON Patch applicability.

## Heuristic Fallback (SC003)

When LLM disabled or returns zero ops for an Ingress suggestion:

- Add `/spec/ingressClassName` (value `web`) if missing.
- If host present and no `spec.tls`, add minimal TLS stanza with secret `<name>-tls`.
  Deterministic → reproducible in CI.

## Conflict Semantics

- Duplicate op (same op+path+value) skipped (counted as `skipped_duplicates`).
- Same path with different value/op => conflict; new op appended (Kubernetes apply order semantics) and counted + optionally detailed with `--verbose`.

## Logging Events

Structured JSON (see `src/llm/logger.py`) includes events:

- `suggest`, `suggest.store`, `suggest.heuristic`
- `merge.add`, `merge.duplicate`, `merge.conflict`, `merge.summary`, `merge.summary.final`
- `merge.validate_ops` (failed suggestion rejected)

## Typical CI Pattern

1. Generate violations (custom script) → `violations.json`.
2. Run `suggest` (LLM enabled or not).
3. Optionally lint `suggestions.json` (check meta.valid > 0).
4. Run `merge-suggestions --approve <indices>` (explicit) → exit code 0 expected. Treat 2 as “needs human review”.
5. Commit `patch.json` or open PR with diff.

## Future Ideas

- JSON summary mode for merge conflicts.
- Score/rank suggestions (confidence) before approval.
- Apply / dry-run chain invoking cluster (live mode).
- Additional heuristics for more rules.

## Development

Tests use `pytest`. Run all:

```
uv run pytest -q
```

## License

TBD (add appropriate license file before distribution).
