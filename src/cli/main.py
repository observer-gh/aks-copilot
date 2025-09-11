# src/cli/main.py
import json
import pathlib
import typer
from src.inspect.storageclass import inspect_storageclass

app = typer.Typer(help="k3s→AKS Copilot (MVP)")


@app.command()
def fix(filepath: pathlib.Path):
    """
    Read a single YAML file and:
    - write report.md (violations summary)
    - write patch.json (JSON Patch ops to replace storageClassName to managed-csi)
    """
    if not filepath.exists():
        typer.echo(f"[ERR] file not found: {filepath}", err=True)
        raise typer.Exit(code=1)

    text = filepath.read_text(encoding="utf-8")
    violations = inspect_storageclass(text)

    # Always write files (MVP)
    report_path = pathlib.Path("report.md")
    patch_path = pathlib.Path("patch.json")

    # Build report
    lines = ["# Migration Copilot Report", "", "**Violations Found**"]
    if not violations:
        lines.append("")
        lines.append("- None")
    else:
        for v in violations:
            lines += [
                "",
                f"- ID: {v['id']}",
                f"  Resource: {v['resource']}",
                f"  Path: {v['path']}",
                f"  Found: {v['found']}",
                f"  Expected: {v['expected']}",
                f"  Severity: {v['severity']}",
                "  Why: k3s local-path is single-node only; AKS requires managed CSI storage for reliability."
            ]
    report_path.write_text("\n".join(lines), encoding="utf-8")

    # Build JSON Patch ops (one replace per violation)
    patch_ops = []
    for v in violations:
        patch_ops.append({
            "op": "replace",
            "path": v["path"],
            "value": v["expected"]
        })
    patch_path.write_text(json.dumps(patch_ops, indent=2), encoding="utf-8")

    typer.echo(f"Wrote {report_path} and {patch_path}")
    raise typer.Exit(code=0)


@app.command("fix-folder")
def fix_folder(dirpath: pathlib.Path):
    """
    Read all *.yml|*.yaml under <dir> (non-recursive), aggregate violations,
    write report.md + patch.json.
    """
    if not dirpath.exists() or not dirpath.is_dir():
        typer.echo(f"[ERR] not a directory: {dirpath}", err=True)
        raise typer.Exit(code=1)

    files = sorted([*dirpath.glob("*.yml"), *dirpath.glob("*.yaml")])
    if not files:
        typer.echo("[WARN] no *.yml|*.yaml found")
        raise typer.Exit(code=0)

    all_violations = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        vs = inspect_storageclass(text)
        # tag each violation with filename for report readability
        for v in vs:
            v = dict(v)
            v["file"] = str(f)
            all_violations.append(v)

    # write report.md
    report_path = pathlib.Path("report.md")
    lines = ["# Migration Copilot Report", "", "**Violations Found**"]
    if not all_violations:
        lines += ["", "- None"]
    else:
        for v in all_violations:
            lines += [
                "",
                f"- File: {v['file']}",
                f"  ID: {v['id']}",
                f"  Resource: {v['resource']}",
                f"  Path: {v['path']}",
                f"  Found: {v['found']}",
                f"  Expected: {v['expected']}",
                f"  Severity: {v['severity']}",
                "  Why: k3s local-path is single-node; AKS needs managed CSI."
            ]
    report_path.write_text("\n".join(lines), encoding="utf-8")

    # write patch.json (one op per violation)
    patch_ops = [{"op": "replace", "path": v["path"],
                  "value": v["expected"]} for v in all_violations]
    pathlib.Path("patch.json").write_text(
        json.dumps(patch_ops, indent=2), encoding="utf-8")

    typer.echo(
        f"Wrote {report_path} and patch.json ({len(all_violations)} violations across {len(files)} files).")


@app.command("fix-tree")
def fix_tree(dirpath: pathlib.Path):
    """
    Recursively read all *.yml|*.yaml under <dir>, aggregate violations,
    then write a single report.md + patch.json in CWD.
    """
    if not dirpath.exists() or not dirpath.is_dir():
        typer.echo(f"[ERR] not a directory: {dirpath}", err=True)
        raise typer.Exit(code=1)

    files = sorted(list(dirpath.rglob("*.yml")) +
                   list(dirpath.rglob("*.yaml")))
    if not files:
        typer.echo("[WARN] no *.yml|*.yaml found")
        raise typer.Exit(code=0)

    all_violations = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception as e:
            typer.echo(f"[WARN] skip {f}: {e}")
            continue
        for v in inspect_storageclass(text):
            vv = dict(v)
            vv["file"] = str(f)
            all_violations.append(vv)

    # report.md
    lines = ["# Migration Copilot Report", "", "**Violations Found**"]
    if not all_violations:
        lines += ["", "- None"]
    else:
        for v in all_violations:
            lines += [
                "",
                f"- File: {v['file']}",
                f"  ID: {v['id']}",
                f"  Resource: {v['resource']}",
                f"  Path: {v['path']}",
                f"  Found: {v['found']}",
                f"  Expected: {v['expected']}",
                f"  Severity: {v['severity']}",
                "  Why: k3s local-path is single-node; AKS needs managed CSI.",
            ]
    pathlib.Path("report.md").write_text("\n".join(lines), encoding="utf-8")

    # patch.json
    patch_ops = [{"op": "replace", "path": v["path"],
                  "value": v["expected"]} for v in all_violations]
    pathlib.Path("patch.json").write_text(
        json.dumps(patch_ops, indent=2), encoding="utf-8")

    typer.echo(
        f"Wrote report.md and patch.json ({len(all_violations)} violations across {len(files)} files).")


@app.command("fix-per-file")
def fix_per_file(dirpath: pathlib.Path):
    """
    For each *.yml|*.yaml in <dir> (non-recursive), write
    report_<name>.md and patch_<name>.json next to the file.
    """
    if not dirpath.exists() or not dirpath.is_dir():
        typer.echo(f"[ERR] not a directory: {dirpath}", err=True)
        raise typer.Exit(code=1)

    files = sorted([*dirpath.glob("*.yml"), *dirpath.glob("*.yaml")])
    if not files:
        typer.echo("[WARN] no *.yml|*.yaml found")
        raise typer.Exit(code=0)

    total_v = 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        violations = inspect_storageclass(text)
        base = f.stem  # filename without extension
        report_path = f.with_name(f"report_{base}.md")
        patch_path = f.with_name(f"patch_{base}.json")

        # report
        lines = ["# Migration Copilot Report", "",
                 f"**File:** {f.name}", "", "**Violations Found**"]
        if not violations:
            lines += ["", "- None"]
        else:
            for v in violations:
                lines += [
                    "",
                    f"- ID: {v['id']}",
                    f"  Resource: {v['resource']}",
                    f"  Path: {v['path']}",
                    f"  Found: {v['found']}",
                    f"  Expected: {v['expected']}",
                    f"  Severity: {v['severity']}",
                    "  Why: k3s local-path is single-node; AKS needs managed CSI.",
                ]
        report_path.write_text("\n".join(lines), encoding="utf-8")

        # patch
        ops = [{"op": "replace", "path": v["path"], "value": v["expected"]}
               for v in violations]
        patch_path.write_text(json.dumps(ops, indent=2), encoding="utf-8")

        total_v += len(violations)

    typer.echo(
        f"Wrote per-file reports/patches for {len(files)} files ({total_v} violations total).")


@app.command()
def validate(filepath: pathlib.Path):
    """
    Read a single YAML file and print SC001 violations (no files written).
    """
    if not filepath.exists():
        typer.echo(f"[ERR] file not found: {filepath}", err=True)
        raise typer.Exit(code=1)

    text = filepath.read_text(encoding="utf-8")
    violations = inspect_storageclass(text)

    if not violations:
        typer.echo("No violations.")
        raise typer.Exit(code=0)

    typer.echo("# Violations")
    for v in violations:
        typer.echo(
            f"- {v['id']} {v['resource']} {v['path']} found={v['found']} → expected={v['expected']}")


if __name__ == "__main__":
    app()
