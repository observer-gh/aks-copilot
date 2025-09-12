from src.explain.loader import load_explanation


def format_violations(violations):
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
        else:
            lines.append("  Patch: manual (no auto-fix)")
        exp = load_explanation(v["id"])
        if exp.get("why"):
            lines.append(f"  Why: {exp['why']}")
        if exp.get("source"):
            lines.append(f"  Source: {exp['source']}")
        lines.append("")  # blank line between entries
    lines.append("")
    lines.append(f"Total violations: {len(violations)}")
    return lines
