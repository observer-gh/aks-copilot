Handoff: Story 1.1 — Project Setup & CLI Foundation

Goal

Implement Story 1.1: initialize the Python project layout (if missing) and deliver a working CLI command `copilot fix-folder <directory>` that finds YAML manifests (non-recursive) and exits cleanly.

Context

- Planning, PRD, architecture, and sharded epics are complete. Stories were generated and stored in `docs/stories/`.
- This handoff is scoped to the minimal implementation needed for Story 1.1 so subsequent Dev stories can build on it.

Acceptance criteria (must pass)

1. A Python project structure exists (project metadata in `pyproject.toml`, source files under `src/`).
2. A console script `copilot` is registered and points to the Typer `app` in `src/cli/main.py` (entrypoint `copilot fix-folder`).
3. Running `copilot fix-folder <directory>` (non-recursive) prints a list of found `*.yml`/`*.yaml` files, or prints a warning and exits code 0 if none found.
4. A unit test exists that runs the CLI against `tests/fixtures/` and asserts the expected file names are printed.
5. All tests pass with `pytest`.

Files to inspect/edit

- `pyproject.toml` — ensure `[project.scripts] copilot = "src.cli.main:app"` is present (already added).
- `src/cli/main.py` — ensure `fix-folder` command behavior matches acceptance criteria (non-recursive search, prints files, exits with appropriate codes).
- `tests/test_storageclass.py` — existing tests for inspectors; keep untouched unless needed.
- Add: `tests/test_cli.py` — CLI test using `typer.testing.CliRunner` to invoke `copilot fix-folder tests/fixtures` and assert visible output.

Suggested test (pytest)

- Create `tests/test_cli.py` with content (example):

```python
from typer.testing import CliRunner
from src.cli.main import app


def test_fix_folder_lists_files():
    runner = CliRunner()
    result = runner.invoke(app, ["fix-folder", "tests/fixtures"])
    assert result.exit_code == 0
    assert "deploy_bad.yml" in result.stdout
```

Developer notes & constraints

- Use `typer` for CLI (already used). Keep the `app` Typer instance in `src/cli/main.py`.
- Non-recursive file discovery only: use `Path.glob("*.yml")` and `Path.glob("*.yaml")` in the specified directory.
- The CLI must not attempt to contact external services or the cluster for this story.
- Keep logic minimal and test-driven: implement only what's required for this story.
- Make changes in a feature branch `feat/story-1.1-cli` and open a PR against `main` when ready.

Commands for developer

- Install dev dependencies and editable package:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[test]
```

- Run tests:

```bash
pytest -q
```

- Run the CLI locally (after `pip install -e .`):

```bash
copilot fix-folder tests/fixtures
```

PR checklist

- [ ] Tests added and passing
- [ ] `pyproject.toml` updated if new runtime deps were needed
- [ ] Minimal, well-documented changes in `src/cli/main.py`
- [ ] Branch name follows `feat/story-1.1-cli`
- [ ] Short PR description that links to `docs/stories/epic-1-story-1.1-project-setup-cli-foundation.md`

Handoff metadata

- Story reference: `docs/stories/epic-1-story-1.1-project-setup-cli-foundation.md`
- Assigned to: Dev agent (or human dev)
- Priority: high (foundation)

Notes for the Dev agent

- This repo already contains helper modules (inspectors) and tests. Story 1.1 focuses on the CLI foundation only. Keep changes minimal and run the provided pytest.
- If anything in `pyproject.toml` or existing CLI conflicts with these requirements, call out the conflict in the PR description and propose a small, safe fix.
