from typer.testing import CliRunner

from src.cli.main import app


def test_fix_folder_lists_yml_files_and_returns_zero():
    runner = CliRunner()
    result = runner.invoke(app, ["fix-folder", "tests/fixtures"])
    assert result.exit_code == 0
    output = result.output
    # ensure expected fixture YAML filenames are present (non-recursive)
    assert "statefulset_bad.yml" in output
    assert "deploy_bad.yml" in output
