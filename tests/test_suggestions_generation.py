import json
from typer.testing import CliRunner
from src.cli.main import app


def test_suggest_generates_valid_sc003(monkeypatch, tmp_path):
    # violations including an SC003
    violations = [
        {
            "id": "SC003",
            "rule_id": "SC003",
            "file": "ingress_bad.yml",
            "kind": "Ingress",
            "name": "web",
            "path": "/spec",
            "resource": "web"
        }
    ]
    vfile = tmp_path / "violations.json"
    vfile.write_text(json.dumps(violations), encoding="utf-8")

    # monkeypatch generate_suggestion to return deterministic ops
    from src.llm import augment as aug_mod

    def fake_generate(v):
        return {
            "type": "patch_suggestion",
            "ops": [
                {"op": "add", "path": "/spec/ingressClassName", "value": "web"}
            ],
            "explanation": "Add ingressClassName"
        }

    monkeypatch.setattr(aug_mod, "generate_suggestion", fake_generate)
    runner = CliRunner()
    out_sug = tmp_path / "suggestions.json"
    res = runner.invoke(app, ["suggest", str(vfile), "--out", str(out_sug)])
    assert res.exit_code == 0, res.output
    data = json.loads(out_sug.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["meta"]["total"] == 1
    assert data["suggestions"][0]["valid"] is True
