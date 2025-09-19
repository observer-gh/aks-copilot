# Dev Handoff — Story 1.5: Remaining MVP rule checks (SC002, SC003)

Summary

Implement the remaining MVP rule checks and wire them into the existing patch/suggestion flow so the project covers the next set of rules after SC001. Focus on SC002 (container resource requests/limits) as an auto-fixable rule and SC003 (ingress/TLS/class issues) as suggestion-only or LLM-assisted. Deliver test fixtures and unit/CLI tests that exercise the full flow.

Why this matters

- Completes critical rule coverage for the MVP.
- Demonstrates end-to-end inspection → patch generation → dry-run validation for more than one rule.
- Enables early automation for common anti-patterns (missing resource limits, wrong ingress class) and prepares for LLM-suggest flows.

Acceptance criteria

- New inspectors for SC002 and SC003 exist under `src/inspect/` and emit violations with the standard shape used by the patch engine.
- `src/patch/generator.py` updated to produce patch envelopes for SC002 auto-fixes (and skip SC003 for automatic patching, or mark as suggestion-only).
- Fixtures added in `tests/fixtures/` for SC002 and SC003 example manifests.
- Unit tests added:
  - `tests/test_requests_limits.py` — inspector unit tests (happy + failing cases).
  - `tests/test_ingress_class.py` — inspector unit tests for ingress/TLS checks.
  - `tests/test_patch_engine.py` extended to include SC002 patch generation + dry-run validation.
  - `tests/test_patch_cli.py` extended or a new `tests/test_patch_cli_sc002.py` to run `copilot patch` for SC002 and verify dry-run success.
- All tests pass locally with `uv run pytest -q`.

Contract (short)

- Input: YAML manifest text(s) or file(s).
- Inspector output (violation) shape (example):
  {
  "id": "SC002",
  "rule_id": "SC002",
  "file": "tests/fixtures/deployment_no_limits.yml",
  "kind": "Deployment",
  "name": "web-0",
  "path": "/spec/template/spec/containers/0/resources",
  "current": {"requests": {}, "limits": {}},
  "desired": {"requests": {"cpu": "100m", "memory": "128Mi"}, "limits": {"cpu": "250m", "memory": "256Mi"}},
  "message": "missing resource requests/limits"
  }

- Patch op for SC002 (envelope):
  {
  "file": "tests/fixtures/deployment_no_limits.yml",
  "resource": {"kind":"Deployment","name":"web-0"},
  "ops": [
  {"op":"add","path":"/spec/template/spec/containers/0/resources","value": {"requests": {"cpu":"100m","memory":"128Mi"},"limits": {"cpu":"250m","memory":"256Mi"}}}
  ]
  }

Notes on behavior

- SC002 (resource requests/limits): auto-fixable when the desired values can be chosen deterministically from config defaults or a small rule table. Implement as `add` (if missing) or `replace` (if present but empty) depending on the path existence.
- SC003 (ingress class/TLS): suggestion-only by default. Provide clear human-readable suggestion output or LLM-suggested patch via `llm-suggest` command. Do not auto-apply by default.
- Multi-document YAML: inspector should include `resource` selector (kind/name) in the violation so `dry_run_validate` can choose the correct document if a manifest file contains multiple docs.

Files to add / edit

- Add/extend inspectors:
  - `src/inspect/requests_limits.py` — implements SC002 inspector(s).
  - `src/inspect/ingress_class.py` — implements SC003 inspector(s) (or extend existing `inspect/ingress.py`).
- Patch generator:
  - Edit `src/patch/generator.py` to handle `SC002` generation via `add`/`replace` ops and include `resource` selector in envelopes.
- CLI:
  - Optionally extend `copilot patch` with `--manifests-root` to resolve relative manifest paths.
- Tests & fixtures:
  - `tests/fixtures/deployment_no_limits.yml` — Deployment without resource requests/limits.
  - `tests/fixtures/ingress_bad.yml` — Ingress with wrong class or missing TLS.
  - `tests/test_requests_limits.py` — inspector unit tests.
  - `tests/test_ingress_class.py` — inspector unit tests.
  - Extend `tests/test_patch_engine.py` to include SC002.
  - Extend `tests/test_patch_cli.py` or add `tests/test_patch_cli_sc002.py`.

Implementation plan (concrete steps for a Dev)

1. Implement SC002 inspector (`src/inspect/requests_limits.py`):

   - Parse YAML text for Deployment/StatefulSet/DaemonSet `containers` list.
   - For each container, check `resources.requests` and `resources.limits` presence and non-empty values.
   - Create violations where missing, including a `desired` key with defaults pulled from `src.config.get_config()` (config keys: `defaultRequests`, `defaultLimits` or `defaultResources`).

2. Add fixtures:

   - `deployment_no_limits.yml`: small Deployment manifest without resources in containers.

3. Extend `build_patch_ops` in `src/patch/generator.py`:

   - Add case for `SC002` that builds an `add` op to create `resources` at the container index path when missing; use `desired` payload from violation.
   - Ensure envelope includes `file` and `resource` selector for multi-doc files.

4. Write unit tests:

   - `tests/test_requests_limits.py`:
     - Test inspector returns a violation when resources missing.
     - Test desired defaults are included.
   - `tests/test_patch_engine.py` (extend):
     - Use `deployment_no_limits.yml` fixture to generate patches and run `dry_run_validate` to assert success.

5. CLI integration test:

   - Use the existing `copilot patch` command to run the violations file (or write a temporary violations JSON), run `--dry-run`, and assert success.

6. Run tests and iterate until green:
   - `uv run pytest -q` and fix failures quickly.

Edge cases & decisions to document

- Choosing defaults: either store in `config.json`/`pyproject` or codify a minimal default in inspector (preferred: config-driven so owners can tune values).
- Indexing containers: the path uses container index; handle multiple containers per pod and choose the first container for simple POC or include index in violation.
- Add vs replace: create `add` op when the final path is missing (per `dryrun` behavior), use `replace` when the key exists but empty.

Security & safety

- Dry-run only: ensure `copilot patch --dry-run` never writes to cluster.
- No automatic apply without explicit `copilot apply` and human consent.

QA checklist for PR

- [ ] New inspector files added and imported where appropriate.
- [ ] `src/patch/generator.py` updated to support SC002.
- [ ] Fixtures added under `tests/fixtures/`.
- [ ] Tests added and passing locally.
- [ ] `docs/handoffs/dev-handoff-1.5.md` reviewed by SM/PO for acceptance.

Estimated effort

- SC002 only (end-to-end): ~1–2 hours.
- SC002 + SC003 + tests: ~2–4 hours.

Assignment block (copy-paste)

Task: Implement Story 1.5 — SC002 (auto-fix) and SC003 (suggest)
Priority: Medium-High
Deliverables:

- `src/inspect/requests_limits.py`
- `src/inspect/ingress_class.py` (or extend existing)
- `src/patch/generator.py` updated
- Fixtures + tests under `tests/fixtures/` and `tests/test_*.py`
- Integration test to exercise `copilot patch --dry-run`

Acceptance tests:

- `uv run pytest -q` passes on branch.
- `copilot patch --dry-run` validates SC002 patches for fixture manifests.

Reviewer notes

- Keep the logic modular: add a small dispatch map in `src/patch/generator.py` so new rules can be registered easily.
- Prefer `config`-driven defaults for resource sizes.

---

If you want I can also implement SC002 now (fast POC) and run tests; just confirm and I will proceed.
