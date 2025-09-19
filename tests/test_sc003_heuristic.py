import json
import textwrap
from typer.testing import CliRunner
from src.cli.main import app


def _write_ingress(path, with_class=False, with_tls=False, host="example.com"):
    ingress = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {"name": "web"},
        "spec": {
            "rules": [{"host": host, "http": {"paths": []}}]
        }
    }
    if with_class:
        ingress["spec"]["ingressClassName"] = "web"
    if with_tls:
        ingress["spec"]["tls"] = [{"hosts": [host], "secretName": "web-tls"}]
    import yaml
    path.write_text(yaml.safe_dump(ingress), encoding="utf-8")


def test_sc003_heuristic_adds_class_and_tls(tmp_path, monkeypatch):
    manifest = tmp_path / "ing.yml"
    _write_ingress(manifest, with_class=False, with_tls=False)
    violations = [
        {"id": "SC003", "rule_id": "SC003", "file": str(
            manifest), "kind": "Ingress", "name": "web", "path": "/spec"}
    ]
    vfile = tmp_path / "violations.json"
    vfile.write_text(json.dumps(violations), encoding="utf-8")
    # monkeypatch generate_suggestion to return empty so heuristic triggers
    from src.llm import augment as aug_mod
    monkeypatch.setattr(aug_mod, "generate_suggestion", lambda v: {
                        "type": "patch_suggestion", "ops": []})
    runner = CliRunner()
    out_sug = tmp_path / "suggestions.json"
    res = runner.invoke(app, ["suggest", str(vfile), "--out", str(out_sug)])
    assert res.exit_code == 0, res.output
    data = json.loads(out_sug.read_text(encoding="utf-8"))
    ops = data["suggestions"][0]["ops"]
    paths = {o["path"] for o in ops}
    assert "/spec/ingressClassName" in paths
    assert "/spec/tls" in paths


def test_sc003_heuristic_only_class(tmp_path, monkeypatch):
    manifest = tmp_path / "ing.yml"
    _write_ingress(manifest, with_class=False, with_tls=True)
    violations = [
        {"id": "SC003", "rule_id": "SC003", "file": str(
            manifest), "kind": "Ingress", "name": "web", "path": "/spec"}
    ]
    vfile = tmp_path / "violations.json"
    vfile.write_text(json.dumps(violations), encoding="utf-8")
    from src.llm import augment as aug_mod
    monkeypatch.setattr(aug_mod, "generate_suggestion", lambda v: {
                        "type": "patch_suggestion", "ops": []})
    runner = CliRunner()
    out_sug = tmp_path / "suggestions.json"
    res = runner.invoke(app, ["suggest", str(vfile), "--out", str(out_sug)])
    assert res.exit_code == 0
    data = json.loads(out_sug.read_text(encoding="utf-8"))
    ops = data["suggestions"][0]["ops"]
    paths = {o["path"] for o in ops}
    assert "/spec/ingressClassName" in paths
    assert not any(o["path"] == "/spec/tls" for o in ops)


def test_sc003_heuristic_only_tls(tmp_path, monkeypatch):
    manifest = tmp_path / "ing.yml"
    # ingress already has class but no tls
    _write_ingress(manifest, with_class=True, with_tls=False)
    violations = [
        {"id": "SC003", "rule_id": "SC003", "file": str(
            manifest), "kind": "Ingress", "name": "web", "path": "/spec"}
    ]
    vfile = tmp_path / "violations.json"
    vfile.write_text(json.dumps(violations), encoding="utf-8")
    from src.llm import augment as aug_mod
    monkeypatch.setattr(aug_mod, "generate_suggestion", lambda v: {
                        "type": "patch_suggestion", "ops": []})
    runner = CliRunner()
    out_sug = tmp_path / "suggestions.json"
    res = runner.invoke(app, ["suggest", str(vfile), "--out", str(out_sug)])
    assert res.exit_code == 0
    data = json.loads(out_sug.read_text(encoding="utf-8"))
    ops = data["suggestions"][0]["ops"]
    paths = {o["path"] for o in ops}
    assert "/spec/ingressClassName" not in paths
    assert "/spec/tls" in paths
