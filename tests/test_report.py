from pathlib import Path
from typer.testing import CliRunner
from src.cli.main import app


def test_report_generated_for_fixture(tmp_path):
    runner = CliRunner()
    # run CLI against tests/fixtures (repo-relative)
    result = runner.invoke(app, ["fix-folder", "tests/fixtures"])
    assert result.exit_code == 0

    report = Path("report.md")
    assert report.exists(), "report.md should be created"
    text = report.read_text(encoding="utf-8")
    assert "Total violations:" in text
    # cleanup
    report.unlink()


def test_report_and_patch_contain_rules_for_fixtures(tmp_path):
    """Integration: ensure report and patch include SC00* entries for fixtures"""
    runner = CliRunner()
    result = runner.invoke(app, ["fix-folder", "tests/fixtures"])
    assert result.exit_code == 0

    report = Path("report.md")
    patch = Path("patch.json")
    assert report.exists(), "report.md should be created"
    assert patch.exists(), "patch.json should be created"

    rtext = report.read_text(encoding="utf-8")
    ptext = patch.read_text(encoding="utf-8")

    # expect at least one SC001 (PVC) and one SC002 (missing limits) mentioned
    assert "SC001" in rtext or "SC001" in ptext
    assert "SC002" in rtext or "SC002" in ptext

    # cleanup
    report.unlink()
    patch.unlink()
