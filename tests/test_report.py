import json
from pathlib import Path
from typer.testing import CliRunner
from src.cli.main import app


def test_report_generated_for_fixture(tmp_path, monkeypatch):
    # Create a dummy config.json to avoid using the default one with ollama
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"llm": "stub"}))

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    # Get the absolute path to the fixtures directory
    fixtures_path = Path(__file__).parent / "fixtures"

    # run from tmp_path to ensure our dummy config is picked up
    # run CLI against tests/fixtures (repo-relative)
    result = runner.invoke(app, ["fix-folder", str(fixtures_path)])
    assert result.exit_code == 0, result.stdout

    report = Path("report.md")
    assert report.exists(), "report.md should be created"
    text = report.read_text(encoding="utf-8")
    assert "Violations Found" in text


def test_report_and_patch_contain_rules_for_fixtures(tmp_path, monkeypatch):
    """Integration: ensure report and patch include SC00* entries for fixtures"""
    # Create a dummy config.json to avoid using the default one with ollama
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"llm": "stub"}))

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    # Get the absolute path to the fixtures directory
    fixtures_path = Path(__file__).parent / "fixtures"
    result = runner.invoke(app, ["fix-folder", str(fixtures_path)])
    assert result.exit_code == 0, result.stdout

    report = Path("report.md")
    patch = Path("patch.json")
    assert report.exists(), "report.md should be created"
    assert patch.exists(), "patch.json should be created"

    rtext = report.read_text(encoding="utf-8")
    ptext = patch.read_text(encoding="utf-8")

    # expect at least one SC001 (PVC) and one SC002 (missing limits) mentioned
    assert "SC001" in rtext
    assert "SC002" in rtext

    patch_data = json.loads(ptext)
    assert len(patch_data) > 0
    assert any(op['path'] == '/spec/storageClassName' for op in patch_data)
