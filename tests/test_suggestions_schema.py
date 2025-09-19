import json
from src.patch.suggestions import write_suggestions, load_suggestions


def test_write_suggestions_wrapper(tmp_path):
    path = tmp_path / "suggestions.json"
    suggestions = [
        {"index": 0, "rule_id": "SC003", "file": "ing.yml", "resource": {
            "kind": "Ingress", "name": "web"}, "ops": [], "valid": True}
    ]
    write_suggestions(suggestions, str(path), rule="SC003")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["meta"]["total"] == 1
    assert isinstance(data["suggestions"], list)
    # loader returns list only
    loaded = load_suggestions(str(path))
    assert loaded and loaded[0]["rule_id"] == "SC003"


def test_load_legacy_array(tmp_path):
    # simulate old format (array only)
    legacy = [
        {"index": 0, "rule_id": "SC003", "file": "ing.yml", "resource": {
            "kind": "Ingress", "name": "web"}, "ops": [], "valid": True}
    ]
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(legacy), encoding="utf-8")
    loaded = load_suggestions(str(path))
    assert loaded and loaded[0]["file"] == "ing.yml"
