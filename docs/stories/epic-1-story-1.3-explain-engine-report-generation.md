# Epic 1 — Story 1.3: Implement the Explain Engine & Report Generation

- As a developer, I want the agent to generate a `report.md` file that explains the violations it found, so that users can understand the issues.

Acceptance Criteria

1. After the agent runs, a `report.md` file is created.
2. The report correctly lists the `storageClassName` violations found in the previous story, including a clear explanation for each.

Tasks

- Implement report generator that formats violations into `report.md`.
- Include file path, resource kind/name, rule violated, and explanation.
- Add unit tests to validate report content from sample violations.
- Wire report generation into the main CLI flow.
