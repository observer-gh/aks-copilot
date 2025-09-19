# Dev Handoff — Story 1.4: Patch engine & patch.json generation

Summary

Create a patch-generation engine that consumes violations (the output of inspectors) and produces a `patch.json` following JSON Patch (RFC 6902) semantics or a closely-matched schema that downstream tools can apply. Also provide a safe dry-run mode to validate patches against manifests without mutating any cluster resources.

Why this matters

- Produces the concrete artifact (patch.json) required by the PRD.
- Enables automated/safe remediation workflows and CI integration.
- Supports reviewable, testable changes before application to clusters.

Success criteria (Acceptance criteria)

- A new module `src/patch/generator.py` that exposes a function `build_patch_ops(violations: List[dict]) -> List[dict]`.
- A new module `src/patch/dryrun.py` that can validate generated patches against manifests (no cluster writes) and returns simulation results.
- CLI integration: `copilot patch` command that can read violations, emit `patch.json`, and optionally `--dry-run` to validate.
- Unit tests under `tests/test_patch_engine.py` that cover:
  - Patch op generation for a representative SC001 violation.
  - Writing a `patch.json` and reloading it as valid JSON.
  - Dry-run validation against YAML fixtures (no external cluster API required).
- Example fixtures in `tests/fixtures/` including a violation input and a target manifest file for dry-run.
- All tests pass locally with `uv run pytest -q`.

Contract (short)

- Input: List of violation objects (see Data shape below).
- Output: List of JSON Patch operations (each op: {op, path, value} or {op, path, from}).
- Error modes:
  - Invalid violation shape -> raise ValueError (covered by tests).
  - Incompatible target (path not found) -> in dry-run return failure entry (do not raise by default unless `--strict`).

Data shapes

- Violation (one example):
  {
  "rule_id": "SC001",
  "file": "examples/pvc_bad.yml",
  "kind": "PersistentVolumeClaim",
  "name": "data-myapp-0",
  "path": "/spec/storageClassName",
  "current": "local-path",
  "desired": "standard",
  "message": "storageClassName is 'local-path' which is disallowed"
  }

- JSON Patch op (RFC 6902 style simple ops we will use):
  [
  { "op": "replace", "path": "/spec/storageClassName", "value": "standard" }
  ]

Notes:

- For K8s resource patches stored as separate file-level patches you can wrap ops per-file using an envelope type in `patch.json`:
  {
  "file": "examples/pvc_bad.yml",
  "resource": {"kind":"PersistentVolumeClaim","name":"data-myapp-0"},
  "ops": [ {"op":"replace","path":"/spec/storageClassName","value":"standard"} ]
  }

Suggested files to add / edit

- Add: `src/patch/generator.py` — builds patch ops from violations.
- Add: `src/patch/dryrun.py` — validates patch ops against YAML manifests (fixtures) without connecting to a cluster.
- Edit: `src/cli/main.py` — add a `patch` command with flags `--violations`, `--out`, `--dry-run`, `--strict`.
- Add tests:
  - `tests/test_patch_engine.py` — covers generator and dry-run.
  - `tests/fixtures/violations_sc001.json` — sample violations list.
  - `tests/fixtures/pvc_bad.yml` — sample manifest to validate against.

Implementation plan (developer steps)

1. Design the minimal Violation -> Patch mapping rules.

   - For rule SC001: replace the `storageClassName` value with `desired`.
   - For future rules: include a small registry mapping `rule_id` -> generator function to keep generator modular.

2. Implement `build_patch_ops(violations)` in `src/patch/generator.py`:

   - Validate incoming shape (required keys: rule_id, file, path, desired).
   - For each violation produce an op envelope: {file, resource, ops: [ ...RFC6902 ops... ]}.
   - Return list of envelopes.

3. Implement `write_patch_json(patches, out_path)` util to dump the JSON file with an informative header (no comments in JSON, but metadata field ok).

4. Implement `dry_run_validate(patches, manifests_root)` in `src/patch/dryrun.py`:

   - Load each referenced manifest from `file` (relative path) or optional `manifests_root`.
   - Parse YAML to Python object.
   - For each op, walk the JSON pointer path and confirm the target exists and the op is applicable (e.g., `replace` requires the path exist).
   - Return a structured result list: {file, resource, success: bool, details: str}
   - Provide `--strict` option to turn failures into exceptions / non-zero CLI exit.

5. Integrate CLI: Add `patch` command in `src/cli/main.py` that:

   - Reads `violations.json` (or produces them by calling `src/report/writer` if desired).
   - Calls `build_patch_ops` and writes `patch.json`.
   - If `--dry-run`, calls `dry_run_validate` and prints results (and exit non-zero if strict and any false).

6. Add unit tests:
   - `test_build_patch_ops_single_replace`:
     - Load `tests/fixtures/violations_sc001.json` as input.
     - Call `build_patch_ops()` and assert length and op match expected structure.
   - `test_patch_json_write_and_read`:
     - Build a sample patch envelope, write via `write_patch_json`, read file back with `json.load` and assert equality.
   - `test_dry_run_validate_success_and_failure`:
     - Use `tests/fixtures/pvc_bad.yml` (where current storageClassName is local-path) and the generated patch to replace with `standard`.
     - Validate dry-run returns success if path exists and op would change value; returns failure if path not found.

Examples & snippets (for the dev)

- Minimal `build_patch_ops` usage example:

  from src.patch.generator import build_patch_ops
  violations = [{
  "rule_id":"SC001",
  "file":"tests/fixtures/pvc_bad.yml",
  "path":"/spec/storageClassName",
  "current":"local-path",
  "desired":"standard",
  }]
  patches = build_patch_ops(violations)

  # patches -> [{"file":"tests/fixtures/pvc_bad.yml","ops":[{"op":"replace","path":"/spec/storageClassName","value":"standard"}]}]

- Example CLI usage (integration):

  copilot patch --violations tests/fixtures/violations_sc001.json --out patch.json --dry-run

Edge cases and decisions

- When the target resource is multi-document YAML file, the patch envelope should include a selector (kind/name) so the dry-run loader picks the right document index.
- For `add` ops to non-existent paths, `dry_run_validate` should optionally support creating parent path checks or return a clear failure indicating missing path.
- The project currently formats violations with `rule_id`, `file`, `path`, `current`, `desired` in earlier stages — ensure the generator expects that shape. If not present, implement a small shape transformer / adapter.
- Avoid connecting to a real cluster during dry-run; prefer manifest-file validation and YAML parsing.

Security & safety

- Never apply patches to a live cluster unless the CLI command is explicitly `apply` and the user consents.
- The `--dry-run` mode must not call Kubernetes API with write verbs. If you choose to use `kubectl` for validation, use `--dry-run=client` and prefer file-based checks to be deterministic and testable.

QA checklist for PR

- [ ] New modules `src/patch/generator.py` and `src/patch/dryrun.py` added and imported as needed.
- [ ] `src/cli/main.py` includes `patch` command with tests for CLI invocation.
- [ ] Unit tests added (`tests/test_patch_engine.py`) and fixtures added under `tests/fixtures/`.
- [ ] All tests pass locally via `uv run pytest -q`.
- [ ] Confirm `patch.json` output loads with `json.load` and conforms to the envelope schema in this doc.

Estimated effort

A single developer with project familiarity: 3–6 hours.

- Generator + tests: 2–3 hours.
- Dry-run validator + tests: 1–2 hours.
- CLI wiring and docs: 1 hour.

Assignment block (copy-paste friendly)

Task: Implement Story 1.4 — Patch engine & patch.json generation
Priority: High (enables FR2 and end-to-end flow)
Deliverables:

- `src/patch/generator.py`
- `src/patch/dryrun.py`
- CLI `patch` command in `src/cli/main.py`
- Unit tests: `tests/test_patch_engine.py` + fixtures
- Example `patch.json` produced from fixtures

Acceptance tests (automated):

- `pytest` passes with new tests.
- Running `copilot patch --violations tests/fixtures/violations_sc001.json --out patch.json --dry-run` returns a clear success and prints the patch content.

Notes for reviewer

- Keep generator modular: add a `dispatch` by `rule_id` so future rules are pluggable.
- Keep dry-run file-based and deterministic; only use kubectl as a last resort behind a flag.

---

If you want, I can implement Story 1.4 now: I will create the new modules, add unit tests and fixtures, wire the CLI, and run the test suite. Confirm if you'd like me to implement it now or just keep this as a handoff file to assign to a Dev agent.
