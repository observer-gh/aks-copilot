# src/cli/main.py
from src.patch.llm.runner import suggest_sc002_ops
from src.patch.dryrun import dry_run_apply
from src.config import get_config
from src.llm.logger import log_llm
import json
import os
import pathlib
import typer
from src.inspect.storageclass import inspect_storageclass
from src.explain.loader import load_explanation
from src.inspect.requests_limits import inspect_requests_limits
from src.inspect.ingress import inspect_ingress_class
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
    violations += inspect_ingress_class(text)

    # set manual or auto patch mode
    for v in violations:
        v["patch"] = "manual"
        if v.get("id") == "SC001" and path_exists_in_yaml(text, v["path"]):
            v["patch"] = "auto"

    # try LLM lane for SC002 (per container)
    extra_ops = []
    for v in violations:
        if v.get("id") != "SC002":
            continue
        # infer container_path and kind
        path = v["path"]  # e.g. /spec/template/spec/containers/0/resources
        container_path = path.rsplit("/resources", 1)[0]
        # container index
        try:
            idx = int(container_path.split("/containers/")[1].split("/")[0])
        except Exception:
            idx = 0
        # kind heuristic (good enough for MVP)
        kind = "Deployment" if "/spec/template/spec/" in container_path else "Pod"

        ops, reason = suggest_sc002_ops(kind, idx, text, str(filepath))
        if ops:
            v["patch"] = "auto"
            extra_ops.extend(ops)
            log_llm({"file": str(filepath), "rule": "SC002",
                     "stage": "llm", "ok": True, "ops": len(ops)})
        else:
            v["patch"] = "manual"  # keep manual if validator rejected
            log_llm({"file": str(filepath), "rule": "SC002",
                     "stage": "llm", "ok": False, "reason": reason})

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

    # write patch.json: SC001 ops (deterministic) + SC002 ops (LLM if valid)
    sc001_ops = build_patches([v for v in violations if v.get(
        "patch") == "auto" and v["id"] == "SC001"], use_live=False)
    patch_ops = sc001_ops + extra_ops

    # before writing patch.json, dry-run guard
    ok, reason = dry_run_apply(text, patch_ops)
    log_llm({"file": str(filepath), "rule": "ALL", "stage": "dryrun",
             "ok": ok, "reason": ("" if ok else reason)})
    if not ok:
        # if any op would fail, downgrade SC002 to manual and drop its ops
        # keep SC001 deterministic ops only
        patch_ops = [op for op in patch_ops if op.get("op") == "replace"]

    patch_path.write_text(json.dumps(patch_ops, indent=2), encoding="utf-8")

    typer.echo(f"Wrote {report_path} and {patch_path}")
    raise typer.Exit(code=0)


@app.command("fix-folder")
def fix_folder(dirpath: pathlib.Path, live: bool = typer.Option(False, "--live", help="Probe cluster for StorageClasses")):
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
    # show files found for user visibility (basic CLI behavior)
    typer.echo(f"Found {len(files)} files:")
    for f in files:
        typer.echo(f"- {f.name}")

    extra_ops = []
    all_violations = []

    for f in files:
        text = f.read_text(encoding="utf-8")
        vs = inspect_storageclass(text)
        vs += inspect_requests_limits(text)
        vs += inspect_ingress_class(text)

        # before aggregating:
        for v in vs:
            v = dict(v)
            v["file"] = str(f)
            v["patch"] = "manual"
            # SC001 auto if path exists
            if v.get("id") == "SC001" and path_exists_in_yaml(text, v["path"]):
                v["patch"] = "auto"
            all_violations.append(v)

        # after the above loop, add SC002 LLM lane for this file
        file_extra_ops = []
        for v in [vv for vv in all_violations if vv.get("file") == str(f) and vv["id"] == "SC002"]:
            # infer kind/index from path
            container_path = v["path"].rsplit("/resources", 1)[0]
            try:
                idx = int(container_path.split(
                    "/containers/")[1].split("/")[0])
            except Exception:
                idx = 0
            kind = "Deployment" if "/spec/template/spec/" in container_path else "Pod"

            ops, reason = suggest_sc002_ops(kind, idx, text, str(f))
            if ops:
                v["patch"] = "auto"
                file_extra_ops.extend(ops)
                log_llm({"file": str(f), "rule": "SC002",
                         "stage": "llm", "ok": True, "ops": len(ops)})
            else:
                v["patch"] = "manual"
                log_llm({"file": str(f), "rule": "SC002",
                         "stage": "llm", "ok": False, "reason": reason})

        # accumulate to global
        extra_ops.extend(file_extra_ops)

    # write report.md
    report_path = pathlib.Path("report.md")
    lines = ["# Migration Copilot Report", "", "**Violations Found**"]
    if not all_violations:
        lines += ["", "- None"]
    else:
        # Get live StorageClass info if using --live flag
        live_info = None
        if live:
            from src.patch.generator import sc001_patch_ops
            try:
                _, chosen_sc, live_set = sc001_patch_ops("", use_live=True)
                live_info = (chosen_sc, live_set)
            except Exception:
                pass  # fallback gracefully
        lines += format_violations(all_violations, live_info)

    report_path.write_text("\n".join(lines), encoding="utf-8")

    # write patch.json: SC001 ops (deterministic) + SC002 ops (LLM if valid)
    sc001_ops = build_patches([v for v in all_violations if v.get(
        "patch") == "auto" and v["id"] == "SC001"], use_live=live)
    combined_ops = sc001_ops + extra_ops

    # dry-run against a synthetic YAML = concatenation of all files' texts
    folder_text = ""
    for f in files:
        folder_text += f.read_text(encoding="utf-8") + "\n---\n"

    ok, reason = dry_run_apply(folder_text, combined_ops)
    log_llm({"file": "folder", "rule": "ALL", "stage": "dryrun",
             "ok": ok, "reason": ("" if ok else reason)})
    if not ok:
        # drop LLM-generated adds (SC002) on failure; keep safe SC001 replaces
        combined_ops = sc001_ops

    pathlib.Path("patch.json").write_text(
        json.dumps(combined_ops, indent=2), encoding="utf-8")

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
        vs += inspect_ingress_class(text)
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
        violations += inspect_ingress_class(text)
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
    violations += inspect_ingress_class(text)

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


@app.command("llm-suggest")
def llm_suggest(filepath: pathlib.Path, kind: str = "Deployment", index: int = 0):
    """
    Stub: produce SC002 JSON Patch for one container and validate it.
    """
    if not filepath.exists():
        typer.echo(f"[ERR] file not found: {filepath}", err=True)
        raise typer.Exit(code=1)
    text = filepath.read_text(encoding="utf-8")
    ops, reason = suggest_sc002_ops(kind, index, text, str(filepath))
    if ops:
        typer.echo("🤖 LLM suggested patch:")
        typer.echo(json.dumps(ops, indent=2))
        raise typer.Exit(code=0)
    typer.echo(f"[MANUAL] no valid auto-patch: {reason}")


@app.command("show-config")
def show_config():
    import json as _json
    from pprint import pprint
    cfg = get_config()
    typer.echo(_json.dumps(cfg, indent=2, ensure_ascii=False))


@app.command("patch")
def patch_command(violations: pathlib.Path, out: pathlib.Path = pathlib.Path("patch.json"), dry_run: bool = False, strict: bool = False):
    """
    Generate patch.json from a violations JSON file. Optionally run a dry-run validation against manifests.
    """
    if not violations.exists():
        typer.echo(f"[ERR] violations file not found: {violations}", err=True)
        raise typer.Exit(code=1)

    import json as _json
    from src.patch.generator import build_patch_ops, write_patch_json
    from src.patch.dryrun import dry_run_validate

    try:
        v = _json.loads(violations.read_text(encoding="utf-8"))
    except Exception as e:
        typer.echo(f"[ERR] failed to read violations file: {e}", err=True)
        raise typer.Exit(code=1)

    try:
        patches = build_patch_ops(v)
    except Exception as e:
        typer.echo(f"[ERR] failed to build patches: {e}", err=True)
        raise typer.Exit(code=1)

    write_patch_json(patches, str(out))
    typer.echo(f"Wrote patch file: {out}")

    if dry_run:
        # allow caller to override manifests root via MANIFESTS_ROOT env var
        manifests_root = os.environ.get("MANIFESTS_ROOT", "")
        results = dry_run_validate(
            patches, manifests_root=manifests_root, strict=strict)
        ok = all(r["success"] for r in results)
        for r in results:
            typer.echo(
                f"- {r['file']} -> success={r['success']} details={r['details']}")
        if not ok:
            typer.echo("Dry-run: failures detected", err=True)
            raise typer.Exit(code=2)
        typer.echo("Dry-run: all patches validated")


# --- Story 2.2 additions ---
@app.command("suggest")
def suggest_command(violations: pathlib.Path, out: pathlib.Path = pathlib.Path("suggestions.json"), rule: str = "SC003"):
    """Generate patch suggestions (rule-filtered) using LLM + heuristic fallback (SC003) and write schema-wrapped file."""
    if not violations.exists():
        typer.echo(f"[ERR] violations file not found: {violations}", err=True)
        raise typer.Exit(code=1)
    import json as _json
    from src.llm.augment import generate_resource_suggestions
    from src.patch.validator import validate_patch_ops
    from src.patch.suggestions import write_suggestions
    try:
        vlist = _json.loads(violations.read_text(encoding="utf-8"))
    except Exception as e:
        typer.echo(f"[ERR] cannot parse violations: {e}", err=True)
        raise typer.Exit(code=1)
    if not isinstance(vlist, list):
        typer.echo("[ERR] violations file must be a JSON array", err=True)
        raise typer.Exit(code=1)
    raw = generate_resource_suggestions(vlist, rule_filter=rule)
    suggestions = []
    for idx, r in enumerate(raw):
        ops = r.get("ops", [])
        ok, reason = validate_patch_ops(ops)
        suggestions.append({
            "index": idx,
            "rule_id": r.get("rule_id"),
            "file": r.get("file"),
            "resource": {"kind": r.get("kind"), "name": r.get("name")},
            "ops": ops,
            "explanation": r.get("explanation", ""),
            "valid": ok,
            "reason": ("" if ok else reason),
            "rejected": False,
        })
        log_llm({"event": "suggest.store", "index": idx,
                "rule": r.get("rule_id"), "valid": ok})
    write_suggestions(suggestions, str(out), rule=rule)
    typer.echo(
        f"Wrote {out} ({len(suggestions)} suggestions, {sum(1 for s in suggestions if s['valid'])} valid)")


@app.command("merge-suggestions")
def merge_suggestions_cmd(
    suggestions_file: pathlib.Path = typer.Argument(pathlib.Path(
        "suggestions.json"), help="Path to suggestions.json produced by 'suggest' command"),
    approve: str = typer.Option(
        None, "--approve", help="Comma-separated indices to approve"),
    patch: pathlib.Path = typer.Option(pathlib.Path(
        "patch.json"), "--patch", help="Existing patch.json to merge into (created if missing)"),
    verbose: bool = typer.Option(
        False, "--verbose", help="Print per-conflict detailed information")
):
    """Merge approved suggestions into patch.json (creates or updates)."""
    import json as _json
    from src.patch.suggestions import load_suggestions, filter_approved, merge_suggestions_into_patch
    from src.llm.logger import log_llm

    if not suggestions_file.exists():
        typer.echo(
            f"[ERR] suggestions file not found: {suggestions_file}", err=True)
        raise typer.Exit(code=1)
    suggestions = load_suggestions(str(suggestions_file))
    # parse approvals
    approved_indices = None
    if approve:
        try:
            approved_indices = [int(x.strip())
                                for x in approve.split(',') if x.strip()]
        except ValueError:
            typer.echo(
                "[ERR] invalid --approve list (must be integers)", err=True)
            raise typer.Exit(code=1)
    approved = filter_approved(suggestions, approved_indices)
    invalid_requested = 0
    if approved_indices is not None:
        # indices user asked for that are either missing or invalid
        valid_indices = {s.get("index") for s in suggestions if s.get("valid")}
        for idx in approved_indices:
            if idx not in valid_indices:
                invalid_requested += 1
    # load existing patch if present
    existing = []
    if patch.exists():
        try:
            existing = _json.loads(patch.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except Exception:
            existing = []

    if not approve:
        typer.echo(
            "No specific suggestions approved; auto-approving all valid suggestions.",
            err=True,
        )

    merged_patch, summary = merge_suggestions_into_patch(
        existing_patch=existing, suggestions=approved, collect_details=verbose)

    patch.write_text(_json.dumps(merged_patch, indent=2), encoding="utf-8")
    typer.echo(
        f"Merged suggestions: merged={summary['merged']} duplicates={summary['skipped_duplicates']} conflicts={summary['conflicts']} invalid_requested={invalid_requested}")
    if verbose and summary.get("conflicts"):
        # emit conflict details lines
        for d in summary.get("conflict_details", []):
            prev_v = _json.dumps(d.get("previous")) if d.get(
                "previous") is not None else "null"
            new_v = _json.dumps(d.get("new")) if d.get(
                "new") is not None else "null"
            typer.echo(
                f"CONFLICT file={d.get('file')} path={d.get('path')} previous={prev_v} new={new_v}")
    log_llm({"event": "merge.summary.final", **summary,
            "invalid_requested": invalid_requested})
    exit_code = 0 if (summary['conflicts'] ==
                      0 and invalid_requested == 0) else 2
    raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    app()
