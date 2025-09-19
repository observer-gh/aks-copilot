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
