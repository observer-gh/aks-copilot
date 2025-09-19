import json
import pathlib
from typer.testing import CliRunner

from src.cli import main as cli_main


def test_patch_cli_sc002_dry_run(tmp_path):
    """End-to-end: generate patch.json from violations file and dry-run validate against manifests"""
    runner = CliRunner()

    # prepare manifests root with deployment that has no resources
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    src_manifest = pathlib.Path(
        "tests/fixtures/deployment_no_limits.yml").read_text(encoding="utf-8")
    (manifests_dir / "deploy.yml").write_text(src_manifest, encoding="utf-8")

    # violations file: one SC002 violation referring to deploy.yml
    violations = [
        {
            "id": "SC002",
            "file": "deploy.yml",
            "path": "/spec/template/spec/containers/0/resources",
            "kind": "Deployment",
            "name": "my-deploy",
            "current": {},
            "desired": {"limits": {"cpu": "500m", "memory": "256Mi"}, "requests": {"cpu": "250m", "memory": "128Mi"}}
        }
    ]

    vfile = tmp_path / "violations.json"
    vfile.write_text(json.dumps(violations), encoding="utf-8")

    # run the CLI command: patch --dry-run with manifests_root set via environment
    # The CLI accepts a path to violations and a --dry-run flag; we pass strict to fail on errors
    result = runner.invoke(cli_main.app, [
        "patch",
        str(vfile),
        "--out",
        str(tmp_path / "patch.json"),
        "--dry-run",
        "--strict",
    ], env={"MANIFESTS_ROOT": str(manifests_dir)})

    # CLI should exit 0 and write patch.json
    assert result.exit_code == 0, result.output
    patch_text = (tmp_path / "patch.json").read_text(encoding="utf-8")
    patches = json.loads(patch_text)
    # Expect one envelope for deploy.yml
    assert isinstance(patches, list)
    assert len(patches) == 1
    env = patches[0]
    assert env["file"] == "deploy.yml"
    assert env["ops"] and env["ops"][0]["op"] in ("add", "replace")
