from src.llm import augment as aug
from src.llm.augment import generate_suggestion


def test_generate_suggestion_disabled(monkeypatch):
    monkeypatch.setattr(aug, "get_config", lambda: {"llm": {"enabled": False}})
    v = {"id": "SC002", "path": "/spec/template/spec/containers/0/resources"}
    sug = generate_suggestion(v)
    assert sug["type"] == "patch_suggestion"
    assert isinstance(sug["ops"], list)
    assert len(sug["ops"]) == 0
