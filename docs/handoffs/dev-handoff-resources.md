# Handoff: Integrate `resources.md` (FR3) Into Existing Workflow

Role: Development Agent
Owner: BMAD-Master
Status: Ready
Scope: Implement FR3 without adding a new story number (fold into current flow). Always generate `resources.md` whenever violations are processed (same runs that produce `report.md`).

## Objective

Generate a deterministic `resources.md` file summarizing required Azure resources inferred from the inspected Kubernetes manifests and detected violations. This runs automatically with `fix`, `fix-folder`, and `fix-tree` (no extra flag for MVP).

## Acceptance Criteria

1. Running any of: `copilot fix <file>`, `copilot fix-folder <dir>`, or `copilot fix-tree <dir>` produces (or overwrites) a `resources.md` file in the current working directory.
2. `resources.md` contains: Title, short overview, a markdown table (Resource | Purpose | Required | Reason | Signals) and a "Detected Signals" appendix listing raw triggers (file:kind:name/path).
3. Table rows are deterministic for the same input (ordering stable, e.g. predefined ordering list).
4. Includes only resources whose heuristics matched OR baseline core resources (AKS Cluster, Resource Group) which are always present.
5. No external network calls; all inference based on manifests + existing violation objects.
6. Code covered by unit tests for at least: ingress present, pvc present, private image ref, no optional resources case.
7. Does not introduce regression in existing tests.
8. Failure to generate `resources.md` (unexpected parsing error) must NOT abort the main command: log a warning and still exit 0 if the rest succeeded.
9. Signals column entries are comma‑separated canonical tokens: `file.yaml:Kind/Name` (omit `/Name` if name absent). Limit to max 5 shown then append `+N more`.
10. File overwrites (idempotent) – no in‑place merge.

## Out of Scope (MVP)

- Naming conventions (e.g. rg-myproj-dev) – defer.
- Priority column – defer (design later if needed).
- Emitting Bicep/ARM templates.
- Live Azure subscription queries.

## Heuristic Rules (Initial Set)

| Resource Key      | Display Name                                   | Purpose                     | Trigger Logic                                                                   | Reason Template                           |
| ----------------- | ---------------------------------------------- | --------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------- |
| resourceGroup     | Resource Group                                 | Logical container           | Always include                                                                  | Required for all Azure resources          |
| aksCluster        | AKS Cluster                                    | Run workloads               | Always include                                                                  | Target platform                           |
| containerRegistry | Container Registry (ACR)                       | Store container images      | Any image ref host not in {`docker.io`,`mcr.microsoft.com`}                     | Private/enterprise image hosting detected |
| ingressController | Ingress Controller                             | HTTP(S) routing             | At least one Ingress manifest                                                   | Ingress objects present                   |
| publicIp          | Public IP                                      | Expose ingress externally   | Ingress manifest present                                                        | Needed for external ingress endpoint      |
| storageClass      | Storage Class (Managed)                        | Persistent storage          | SC001 violation or any PVC referencing unspecified/unsupported storageClassName | Storage normalization required            |
| persistentStorage | Persistent Volume (Managed Disk / Azure Files) | Stateful workload storage   | Any PVC manifest                                                                | PVC detected                              |
| logAnalytics      | Log Analytics Workspace                        | Centralized logging/metrics | Always include (baseline observability)                                         | Provide cluster + workload insights       |
| monitor           | Azure Monitor Integration                      | Metrics/alerts pipeline     | Always include (paired with Log Analytics)                                      | Observability baseline                    |
| keyVault          | Key Vault (optional)                           | Secret management           | > SECRET_THRESHOLD distinct Secret refs OR images pulling private registry      | Secure secret lifecycle recommended       |

Notes:

- `SECRET_THRESHOLD = 5` (constant in module) for Key Vault trigger.
- `ORDER = ["resourceGroup","aksCluster","containerRegistry","ingressController","publicIp","storageClass","persistentStorage","logAnalytics","monitor","keyVault"]` ensures stable output ordering.
- Combine `logAnalytics` + `monitor` later if desired; keep split now for easy future removal.

### Extensibility Hooks (keep simple now)

Add future resources by: (1) add key to ORDER; (2) add rule function returning (matched, signals, reason). Keep each rule pure & side‑effect free.

## Data Extraction Signals

Collect during existing `_process_files` loop (no second parse pass needed):

- File list of ingress manifests (kind: Ingress)
- PVC manifests
- Container image hosts (regex split on first `/` unless image starts with `sha256:`)
- Secret references: from `envFrom.secretRef.name`, `env.valueFrom.secretKeyRef.name`, volume type `secret` names.
- Detected violations list (already available) – to check for SC001.
- (Future) Service type LoadBalancer could imply publicIp even without Ingress (out of scope now).

## Implementation Plan

1. Create `src/resources/generator.py` with function:

```python
def infer_resources(violations: list, manifests: list[dict]) -> list[dict]:
    """Return list of resource dicts with keys: id, name, required(bool), reason, signals(list[str])."""
```

2. Add helper `collect_manifest_signals(yaml_text:str, file_path:str) -> list[dict]` returning normalized manifest dicts (kind, name, signals) – or reuse existing parsing approach used for violation detection if accessible.
3. In `src/cli/main.py` inside `_process_files` after writing `report.md`, call new `write_resources(inferred, path="resources.md")` inside a try/except that only logs on failure.
4. Provide stable ordering via predefined list; append unknowns at end.
5. Write markdown with sections:
   - `# Required Azure Resources`
   - Short paragraph
   - Table
   - `## Detected Signals` (bullet list)
6. Add tests: `tests/test_resources_md.py` (create minimal manifests and assert rows set). Use golden substring assertions (no snapshot framework needed).

## Test Cases (Minimum)

1. Ingress only → includes ingressController + publicIp + core rows; excludes storageClass, persistentStorage.
2. PVC only → includes storageClass (if SC001 present or PVC has empty storageClassName) + persistentStorage.
3. Private image (`mycorp.azurecr.io/app:1.0`) → adds containerRegistry.
4. Many secrets (>=6 distinct) → adds keyVault.
5. Empty (no optional triggers) → only core rows (resourceGroup, aksCluster, logAnalytics, monitor).
6. Error injection (malformed YAML) → still produces file with core rows; warning logged.

## File Outputs

- `resources.md` regenerated each run (overwrite). Acceptable diff churn.

## Edge Cases

- Malformed YAML: skip gracefully; still produce file with what was inferred.
- Duplicate manifests (same kind+name): count once.
- Mixed ingress classes: still single ingressController row.

## Deliverables

- New module: `src/resources/generator.py`
- Update to `src/cli/main.py`
- New test file: `tests/test_resources_md.py`
- (Optional) Internal helper: `src/resources/_rules.py` (if separation clarifies logic — defer if overkill now)

## Completion Signal

Post message: "FR3 implemented: resources.md generated" and attach snippet of generated table from a sample run.

---

Proceed with implementation and confirm.
