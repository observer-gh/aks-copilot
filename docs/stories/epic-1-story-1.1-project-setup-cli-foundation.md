# Epic 1 — Story 1.1: Project Setup & CLI Foundation

- As a developer, I want to set up the basic Python project structure and a working CLI command, so that I have a foundation to build the agent's logic on.

Acceptance Criteria

1. A new Python project is initialized (pyproject.toml exists and basic package layout under `src/`).
2. A basic CLI command `copilot fix-folder <directory>` exists and can list all `.yml` files in the provided directory.

Tasks

- Initialize project layout (pyproject.toml, src/, README).
- Implement CLI entry point using `click` or `argparse`.
- Implement function to recursively find `.yml`/`.yaml` files.
- Add a simple unit test validating the CLI finds sample fixture manifests.
- Document the command in `README.md`.

Notes

- Keep implementation minimal and test-driven.
