# src/cli/main.py
import json
import pathlib
import typer
from src.inspect.storageclass import inspect_storageclass
from src.explain.loader import load_explanation
from src.inspect.requests_limits import inspect_requests_limits
from src.report.writer import format_violations
from src.patch.validator import path_exists_in_yaml
from src.patch.generator import build_patches
from src.report.writer import format_violations

from src.patch.generator import build_patches

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
    violations = []
    violations += inspect_storageclass(text)
    violations += inspect_requests_limits(text)

    # set manual or auto patch mode
    for v in violations:
        v["patch"] = "manual"
        if v.get("id") == "SC001" and path_exists_in_yaml(text, v["path"]):
            v["patch"] = "auto"

    # Always write files (MVP)
    report_path = pathlib.Path("report.md")
    patch_path = pathlib.Path("patch.json")

    # Build report
    lines = ["# Migration Copilot Report", "", "**Violations Found**"]
    if not violations:
        lines.append("")
        lines.append("- None")
    else:
        lines += format_violations(violations)
    report_path.write_text("\n".join(lines), encoding="utf-8")

    # Build JSON Patch ops (one replace per violation)
    patch_ops = build_patches(violations)

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
        vs += inspect_requests_limits(text)
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
        lines += format_violations(all_violations)

    report_path.write_text("\n".join(lines), encoding="utf-8")

    # write patch.json (one op per violation)
    patch_ops = build_patches(all_violations)
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
        vs = inspect_storageclass(text)
        vs += inspect_requests_limits(text)
        for v in vs:
            vv = dict(v)
            vv["file"] = str(f)
            all_violations.append(vv)

    # report.md
    lines = ["# Migration Copilot Report", "", "**Violations Found**"]
    if not all_violations:
        lines += ["", "- None"]
    else:
        lines += format_violations(all_violations)

    pathlib.Path("report.md").write_text("\n".join(lines), encoding="utf-8")

    # patch.json
    patch_ops = build_patches(all_violations)
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
        violations += inspect_requests_limits(text)
        base = f.stem  # filename without extension
        report_path = f.with_name(f"report_{base}.md")
        patch_path = f.with_name(f"patch_{base}.json")

        # report
        lines = ["# Migration Copilot Report", "",
                 f"**File:** {f.name}", "", "**Violations Found**"]
        if not violations:
            lines += ["", "- None"]
        else:
            lines += format_violations(violations)
        report_path.write_text("\n".join(lines), encoding="utf-8")

        # patch
        patch_ops = build_patches(violations)
        patch_path.write_text(json.dumps(
            patch_ops, indent=2), encoding="utf-8")

        total_v += len(violations)

    typer.echo(
        f"Wrote per-file reports/patches for {len(files)} files ({total_v} violations total).")


@app.command()
def validate(filepath: pathlib.Path):
    """
    Read a single YAML file and print SC00* violations (no files written).
    """
    if not filepath.exists():
        typer.echo(f"[ERR] file not found: {filepath}", err=True)
        raise typer.Exit(code=1)

    text = filepath.read_text(encoding="utf-8")
    violations = inspect_storageclass(text)
    violations += inspect_requests_limits(text)

    if not violations:
        typer.echo("No violations.")
        raise typer.Exit(code=0)

    typer.echo("# Violations")
    for v in violations:
        typer.echo(
            f"- {v['id']} {v['resource']} {v['path']} found={v['found']} → expected={v['expected']}")


@app.command("apply")
def apply_patch(patchfile: pathlib.Path = pathlib.Path("patch.json")):
    """
    Stub: read patch.json and print planned changes (no real apply).
    """
    if not patchfile.exists():
        typer.echo(f"[ERR] patch not found: {patchfile}", err=True)
        raise typer.Exit(code=1)

    ops = json.loads(patchfile.read_text(encoding="utf-8"))
    if not ops:
        typer.echo("No ops to apply.")
        raise typer.Exit(code=0)

    typer.echo("# Apply Plan (stub)")
    for i, op in enumerate(ops, 1):
        typer.echo(f"{i}. {op['op']} {op['path']} -> {op.get('value')}")
    typer.echo("Apply: simulated OK")


@app.command("health")
def health(namespace: str = "default"):
    """
    Stub: pretend to check pod readiness + events.
    """
    typer.echo(f"# Health (namespace={namespace})")
    typer.echo("Pods Ready: 3/3 (mock)")
    typer.echo("Recent Events: none (mock)")


if __name__ == "__main__":
    app()
