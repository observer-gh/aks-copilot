from src.explain.loader import load_explanation
from src.patch.llm.suggest_sc003 import suggest_sc003_preview


def format_violations(violations, live_info=None):
    lines = []
    for v in violations:
        lines.append(f"**File:** {v.get('file', '<input>')}")
        lines.append(f"- {v['id']} {v['resource']} {v['path']}")
        lines.append(f"  Found: {v['found']}")
        lines.append(f"  Expected: {v['expected']}")
        lines.append(f"  Severity: {v['severity']}")
        mode = v.get("patch", "manual")
        if mode == "auto":
            lines.append("  Patch: auto (JSON Patch prepared)")
            # Add live StorageClass info for SC001
            if v["id"] == "SC001" and live_info:
                chosen_sc, live_set = live_info
                live_classes_str = ', '.join(
                    sorted(live_set)) if live_set else 'n/a'
                lines.append(
                    f"  Note: chose '{chosen_sc}' (live classes: {live_classes_str})")
        else:
            lines.append("  Patch: manual (no auto-fix)")

        # SC003 LLM suggestion (preview only)
        if v["id"] == "SC003":
            preview = suggest_sc003_preview(
                v.get("file", "<input>"), kind="Ingress", path=v["path"])
            if preview:
                lines.append("  LLM suggestion (preview only):")
                # indent multi-line YAML for readability
                for ln in preview.splitlines():
                    lines.append(f"    {ln}")

        exp = load_explanation(v["id"])
        if exp.get("why"):
            lines.append(f"  Why: {exp['why']}")
        if exp.get("source"):
            lines.append(f"  Source: {exp['source']}")
        lines.append("")  # blank line between entries
    lines.append("")
    lines.append(f"Total violations: {len(violations)}")
    return lines
