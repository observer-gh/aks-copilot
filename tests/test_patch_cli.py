from typer.testing import CliRunner
import json
from src.cli.main import app


def test_patch_command_generates_patch_and_dry_run(tmp_path, monkeypatch):
    runner = CliRunner()
    # prepare violations file matching fixtures
    violations = [
        {
            "rule_id": "SC001",
            "file": "tests/fixtures/pvc_bad.yml",
            "path": "/spec/storageClassName",
            "desired": "standard",
        }
    ]
    vfile = tmp_path / "violations.json"
    vfile.write_text(json.dumps(violations), encoding="utf-8")

    result = runner.invoke(
        app, ["patch", str(vfile), "--out", str(tmp_path / "patch.json"), "--dry-run"])
    assert result.exit_code == 0
    assert "Wrote patch file" in result.output
    assert "Dry-run: all patches validated" in result.output
