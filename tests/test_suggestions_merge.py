import json
from typer.testing import CliRunner
from src.cli.main import app


def test_merge_suggestions_subset(monkeypatch, tmp_path):
    suggestions = [
        {"index": 0, "rule_id": "SC003", "file": "ing.yml", "resource": {"kind": "Ingress", "name": "web"},
            "ops": [{"op": "add", "path": "/spec/ingressClassName", "value": "web"}], "valid": True},
        {"index": 1, "rule_id": "SC003", "file": "ing.yml", "resource": {"kind": "Ingress",
                                                                         "name": "web"}, "ops": [{"op": "add", "path": "/metadata/uid", "value": "x"}], "valid": False}
    ]
    sfile = tmp_path / "suggestions.json"
    sfile.write_text(json.dumps(suggestions), encoding="utf-8")
    patchfile = tmp_path / "patch.json"
    runner = CliRunner()
    res = runner.invoke(app, ["merge-suggestions", str(sfile),
                        "--approve", "0", "--patch", str(patchfile)])
    assert res.exit_code == 0, res.output
    patch = json.loads(patchfile.read_text(encoding="utf-8"))
    assert isinstance(patch, list) and len(patch) == 1
    env = patch[0]
    assert env["file"] == "ing.yml"
    assert env["ops"] and env["ops"][0]["path"] == "/spec/ingressClassName"


def test_merge_suggestions_invalid_requested(tmp_path):
    # index 1 is invalid (valid=false) and index 2 does not exist
    suggestions = [
        {"index": 0, "rule_id": "SC003", "file": "ing.yml", "resource": {"kind": "Ingress", "name": "web"},
            "ops": [{"op": "add", "path": "/spec/ingressClassName", "value": "web"}], "valid": True},
        {"index": 1, "rule_id": "SC003", "file": "ing.yml", "resource": {"kind": "Ingress",
                                                                         "name": "web"}, "ops": [{"op": "add", "path": "/metadata/uid", "value": "x"}], "valid": False}
    ]
    sfile = tmp_path / "suggestions.json"
    import json
    sfile.write_text(json.dumps({"schema_version": 1, "generated_at": "t", "rule": "SC003", "meta": {
                     "total": 2, "valid": 1}, "suggestions": suggestions}, indent=2), encoding="utf-8")
    from typer.testing import CliRunner
    from src.cli.main import app
    patchfile = tmp_path / "patch.json"
    runner = CliRunner()
    res = runner.invoke(app, ["merge-suggestions", str(sfile),
                        "--approve", "0,1,2", "--patch", str(patchfile)])
    assert res.exit_code == 2  # invalid indexes requested
    # patch should still contain only the valid op
    patch = json.loads(patchfile.read_text(encoding="utf-8"))
    assert len(
        patch) == 1 and patch[0]["ops"] and patch[0]["ops"][0]["path"] == "/spec/ingressClassName"


def test_merge_conflicts_verbose(tmp_path):
    # existing patch has an op; suggestion introduces conflicting op (same path different value)
    existing_patch = [
        {"file": "ing.yml", "resource": {"kind": "Ingress", "name": "web"}, "ops": [
            {"op": "add", "path": "/spec/ingressClassName", "value": "oldclass"}
        ]}
    ]
    patchfile = tmp_path / "patch.json"
    patchfile.write_text(json.dumps(
        existing_patch, indent=2), encoding="utf-8")

    suggestions = [
        {"index": 0, "rule_id": "SC003", "file": "ing.yml", "resource": {"kind": "Ingress", "name": "web"},
            "ops": [{"op": "add", "path": "/spec/ingressClassName", "value": "newclass"}], "valid": True}
    ]
    sfile = tmp_path / "suggestions.json"
    sfile.write_text(json.dumps(suggestions), encoding="utf-8")

    from typer.testing import CliRunner
    from src.cli.main import app
    runner = CliRunner()
    res = runner.invoke(app, ["merge-suggestions", str(sfile),
                        "--approve", "0", "--patch", str(patchfile), "--verbose"])
    # conflict should cause exit code 2
    assert res.exit_code == 2, res.output
    assert "CONFLICT" in res.output
    assert "/spec/ingressClassName" in res.output
    assert "oldclass" in res.output and "newclass" in res.output
    merged = json.loads(patchfile.read_text(encoding="utf-8"))
    assert len(merged) == 1
    ops = merged[0]["ops"]
    assert len(
        ops) == 2 and ops[0]["value"] == "oldclass" and ops[1]["value"] == "newclass"

    def test_e2e_suggest_merge_sc003(tmp_path, monkeypatch):
        """End-to-end: build violations JSON with an SC003 ingress missing class and tls; run suggest then merge all; verify patch ops."""
        # create a minimal ingress manifest missing ingressClassName and tls with a host so heuristic yields 2 ops
        ingress_yaml = """
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: web
    spec:
      rules:
      - host: example.com
        http:
          paths: []
    """.strip()
        ing_file = tmp_path / "ing.yml"
        ing_file.write_text(ingress_yaml, encoding="utf-8")
        # violations JSON entry minimal fields consumed by generate_resource_suggestions
        violations = [
            {"id": "SC003", "rule_id": "SC003", "file": str(
                ing_file), "kind": "Ingress", "name": "web"}
        ]
        violations_file = tmp_path / "violations.json"
        violations_file.write_text(json.dumps(
            violations, indent=2), encoding="utf-8")
        from typer.testing import CliRunner
        from src.cli.main import app
        runner = CliRunner()
        # run suggest
        res1 = runner.invoke(app, ["suggest", str(
            violations_file), "--rule", "SC003", "--out", str(tmp_path / "suggestions.json")])
        assert res1.exit_code == 0, res1.output
        # run merge-suggestions without --approve to auto-approve all valid
        res2 = runner.invoke(app, ["merge-suggestions", str(tmp_path /
                             "suggestions.json"), "--patch", str(tmp_path / "patch.json")])
        assert res2.exit_code == 0, res2.output
        # inspect patch
        patch = json.loads(
            (tmp_path / "patch.json").read_text(encoding="utf-8"))
        assert len(patch) == 1
        ops = patch[0]["ops"]
        # Heuristic may produce 1 or 2 ops depending on presence of host -> expect at least ingressClassName op
        paths = {o["path"] for o in ops}
        assert "/spec/ingressClassName" in paths
        # when host present, tls should also be added per heuristic
        assert "/spec/tls" in paths


def test_merge_suggestions_auto_approve_notice(tmp_path):
    """Verify that running merge-suggestions without --approve shows an auto-approval notice."""
    suggestions = {
        "schema_version": 1,
        "generated_at": "t",
        "rule": "SC003",
        "meta": {"total": 1, "valid": 1},
        "suggestions": [
            {"index": 0, "rule_id": "SC003", "file": "ing.yml", "resource": {"kind": "Ingress", "name": "web"},
             "ops": [{"op": "add", "path": "/spec/ingressClassName", "value": "web"}], "valid": True}
        ]
    }
    sfile = tmp_path / "suggestions.json"
    sfile.write_text(json.dumps(suggestions), encoding="utf-8")
    patchfile = tmp_path / "patch.json"
    runner = CliRunner()
    # Run without --approve
    res = runner.invoke(
        app, ["merge-suggestions", str(sfile), "--patch", str(patchfile)])
    assert res.exit_code == 0, res.output
    assert "auto-approving all valid suggestions" in res.output
