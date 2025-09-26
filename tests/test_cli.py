import json
from pathlib import Path
from typer.testing import CliRunner

from src.cli.main import app


def test_fix_folder_lists_yml_files_and_returns_zero(tmp_path, monkeypatch):
    # Create a dummy config.json to avoid using the default one with ollama
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"llm": "stub"}))

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()

    # Get the absolute path to the fixtures directory
    fixtures_path = Path(__file__).parent / "fixtures"

    # run from tmp_path to ensure our dummy config is picked up
    result = runner.invoke(app, ["fix-folder", str(fixtures_path)])
    assert result.exit_code == 0, result.stdout
    output = result.stdout
    # ensure expected fixture YAML filenames are present (non-recursive)
    assert "statefulset_bad.yml" in output
    assert "deploy_bad.yml" in output
