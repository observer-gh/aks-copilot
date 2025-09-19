# Dev Handoff — Story 2.1: LLM Integration Foundation

Status: READY FOR DEV
Priority: High (unblocks AI-powered suggestions & future auto-patching)
Owner: Dev Team (after SM approval)
Related Stories: 1.3 (explain/report), 1.4 (patch engine), 1.5 (expanded rules) — this builds atop those outputs.
Depends On: Deterministic inspectors & patch generator already in place.

## Objective

Introduce a safe, pluggable LLM integration layer used for:

1. Enhanced explanations (augment violation/report text)
2. Non-deterministic improvement suggestions (e.g., resource tuning beyond defaults, ingress hardening)
3. (Future) Assisted patch suggestions for rules not fully auto-fixable (e.g., SC003)

This must NOT degrade baseline deterministic behavior: if the LLM is unavailable or returns invalid output, the system falls back cleanly to existing static/RAG explanations.

## Success Criteria (Acceptance)

- Abstraction layer: `LLMClient` (or similar) with a minimal interface (e.g., `generate(prompt: str, *, model: str|None=None, timeout: int|None=None) -> str`).
- Concrete implementation for local Ollama using existing `ollama_generate` in `src/llm/providers.py` (wrap, don’t break).
- Config-driven activation: a config flag (e.g., `config.json` key `llm.enabled: true|false`, plus `llm.provider: "ollama"`, `llm.model: "mistral"`). If disabled, system always uses fallback.
- Prompt templates stored under `src/llm/templates/` (add directory) or reuse existing patch LLM prompts where appropriate. Minimum templates:
  - `explain_violation.txt` — Generate an expanded human-friendly rationale.
  - `suggest_improvement.txt` — Provide structured patch or improvement guidance.
- Safety guardrails:
  - Hard timeout enforced (configurable, default 8s). Timeout => fallback path.
  - Output length cap (e.g., 2k chars) — truncate with notice if exceeded.
  - For patch-like output requests, JSON validation is mandatory; invalid JSON => fallback + log.
- Logging:
  - Use `log_llm` (already in `src/llm/logger.py`) to append JSONL events with: timestamp, request_type, provider, model, latency_ms, success/failure, truncated_prompt_hash, truncated_output_hash.
  - No raw full prompt if it risks leaking content; store hash + first 120 chars.
- Tests (must pass with `uv run pytest -q`):
  - Unit test: stub provider returning canned output for explanation.
  - Unit test: stub provider returns invalid JSON patch suggestion → code rejects & falls back.
  - Timeout test: simulate slow provider (monkeypatch) → fallback used.
  - Fallback test: `llm.enabled=false` ensures deterministic output identical to pre-LLM behavior.
- Documentation: this handoff + new `docs/design/llm-integration.md` summarizing architecture & safety (Dev can create design doc if not existing yet; optional if small diff).

## Non-Goals (Story 2.1)

- Full auto-application of LLM-generated patches — deferred to Story 2.2.
- Multi-provider selection logic (OpenAI, Azure OpenAI, etc.) — can stub; only ensure API shape is extendable.
- RAG embedding updates — existing static/RAG explanation fallback remains unchanged.

## Proposed Architecture

```
CLI / Report Generation
        |
  violation list -----> Explanation Augmentor (LLM optional)
        |                                   |
        | (if suggestion requested)         |
        +----> Suggestion Service (LLM) ----+--> structured suggestion / patch draft
                                                (validate & fallback)
```

### Key Components

| Component                    | Responsibility                                                 | Location (proposed)                           |
| ---------------------------- | -------------------------------------------------------------- | --------------------------------------------- |
| LLMClient (protocol / class) | Thin interface unify providers                                 | `src/llm/client.py`                           |
| OllamaAdapter                | Wraps existing `ollama_generate` with timeout & error handling | `src/llm/providers.py` (or new `adapters.py`) |
| PromptLoader                 | Loads template file, injects structured context                | `src/llm/prompts.py`                          |
| SuggestionValidator          | Validates structured suggestions (JSON Patch shape)            | `src/patch/validator.py` (extend)             |
| ExplainAugmentor             | High-level function used by report writer                      | `src/llm/augment.py`                          |

## Data & Interfaces

### LLMClient Interface Example

```python
class LLMClient:
    def generate(self, prompt: str, *, model: str | None = None, timeout: int | None = None) -> str:
        raise NotImplementedError
```

### Structured Suggestion Output (Goal Shape)

```json
{
  "type": "patch_suggestion",
  "rule_id": "SC003",
  "resource": { "kind": "Ingress", "name": "web-ingress" },
  "ops": [{ "op": "add", "path": "/spec/ingressClassName", "value": "web" }],
  "explanation": "Adding ingressClassName ensures..."
}
```

### Validation Rules

- `type` must be `patch_suggestion`.
- `ops` array must be non-empty & each op has `op`, `path`, and if op in (add, replace) a `value`.
- Reject ops affecting cluster status subresources or unknown top-level keys.
- If invalid: log + fallback explanation (no patch suggestion returned).

## Prompts (Conceptual Snippets)

`explain_violation.txt`:

```
You are an Azure Kubernetes optimization assistant. Given this violation:
Rule: {{rule_id}}
Resource: {{kind}}/{{name}}
Problem: {{message}}
Current fragment:
{{snippet}}
Provide a concise, actionable explanation (max 120 words) and avoid speculative changes.
```

`suggest_improvement.txt` (for SC003 example):

```
You produce JSON only. Given:
Rule: {{rule_id}}
Kind: {{kind}}
Name: {{name}}
Issue: {{message}}
Provide a JSON object with keys: type, rule_id, resource, ops, explanation.
Do not include markdown. Only valid JSON.
```

## Config Additions (example)

```json
{
  "llm": {
    "enabled": true,
    "provider": "ollama",
    "model": "mistral:latest",
    "timeout_seconds": 8,
    "max_output_chars": 2000
  },
  "sc002": {
    "cpu_requests": "100m",
    "mem_requests": "128Mi",
    "cpu_limits": "250m",
    "mem_limits": "256Mi"
  }
}
```

## Logging Event Schema

```json
{
  "ts": "2025-09-19T12:34:56.789Z",
  "phase": "llm_generate",
  "request_type": "suggest_patch",
  "provider": "ollama",
  "model": "mistral:latest",
  "latency_ms": 734,
  "prompt_hash": "sha256:...",
  "output_hash": "sha256:...",
  "truncated": false,
  "fallback": false,
  "success": true
}
```

## Test Plan

| Test                       | Purpose                                           | Method                                         |
| -------------------------- | ------------------------------------------------- | ---------------------------------------------- |
| test_llm_disabled_fallback | Ensure deterministic path when disabled           | set `llm.enabled=false` & call augment/explain |
| test_explain_success       | Normal generation populates enriched explanation  | monkeypatch provider to return canned text     |
| test_suggest_valid_patch   | Valid structured JSON suggestion passes validator | stub returns good JSON                         |
| test_suggest_invalid_json  | Invalid JSON triggers fallback                    | stub returns malformed text                    |
| test_timeout_fallback      | Simulate slow provider -> timeout -> fallback     | stub sleep beyond timeout                      |
| test_output_truncation     | Overlong output truncated & flagged               | stub returns very long string                  |

Coverage threshold: New code paths should be executed in tests; no uncovered critical branch (not enforcing a numeric % here, just functional breadth).

## Edge Cases

- Very large manifests: Only pass minimal snippet (e.g., 30 lines around violation path) into prompt to avoid context bloat.
- Non-ASCII content: Ensure UTF-8 prompt handling; logger uses `ensure_ascii=False` already (OK).
- Concurrent calls: Current usage is synchronous; design interface to allow future async or worker pool.
- Empty or null LLM response: treat as failure -> fallback.

## Risks & Mitigations

| Risk                          | Mitigation                                          |
| ----------------------------- | --------------------------------------------------- |
| LLM hallucinated unsafe patch | Strict validator rejects; fallback explanation only |
| Performance degradation       | Timeout + prompt snippet reduction                  |
| Provider unavailable          | Immediate exception -> fallback path                |
| Sensitive data leak in logs   | Hash & truncate prompts/outputs                     |

## Implementation Steps (Dev Checklist)

1. Create `src/llm/client.py` with interface + `OllamaClient` using existing `ollama_generate` wrapper; add timeout & error translation.
2. Add `src/llm/prompts.py` for loading templates from `src/llm/templates/` directory.
3. Add template files: `explain_violation.txt`, `suggest_improvement.txt`.
4. Implement `augment_explanation(violation)` in `src/llm/augment.py`:
   - If disabled -> return static/RAG fallback.
   - Else build prompt + call client.
   - Enforce length cap & log.
5. Implement `generate_suggestion(violation)` in same or new module.
6. Extend `src/patch/validator.py` for structured suggestion validation (reuse JSON Patch checks from existing code).
7. Wire explanation augmentation into report path (e.g., optional enhancement in `format_violations`). Keep existing behavior if LLM disabled.
8. Add config handling (extend `get_config()` to read `llm` block).
9. Add tests (use monkeypatch to stub client): create `tests/test_llm_explain.py`, `tests/test_llm_suggest.py`.
10. Run full suite; ensure no regressions in existing tests.

## Deliverables

- New code: client, prompts loader, augment functions, validator extension.
- Templates: 2 prompt files.
- Tests: explanation, suggestion, fallback, timeout, invalid JSON.
- Config: extended with `llm` section.
- Logs: verified single JSONL line per call.
- (Optional) design doc summarizing architecture and safety constraints.

## Definition of Done

- All acceptance criteria satisfied.
- `uv run pytest -q` passes.
- Dev reviewer confirms no deterministic regression (compare report output before/after with LLM disabled — identical).
- Security review: no sensitive data stored in logs or prompts beyond violation snippet.

## Assignment Block (Copy/Paste)

Task: Story 2.1 — Implement LLM integration foundation (explanations + suggestions, safe & pluggable)
Priority: High
Deliverables: client, prompt templates, augment & suggestion functions, validator extension, tests, config update, logging.
Exit Criteria: Tests green; disabled-mode output unchanged; structured suggestions validated; fallback robust.

---

SM/PO: Approve & assign to Dev. Dev: Acknowledge, implement checklist, open PR titled: `feat: LLM integration foundation (Story 2.1)`.
