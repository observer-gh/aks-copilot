from src.llm import augment as aug
from src.llm.augment import augment_explanation


def test_augment_explanation_disabled(monkeypatch):
    # Force disabled config by monkeypatching get_config inside augment module
    monkeypatch.setattr(aug, "get_config", lambda: {"llm": {"enabled": False}})
    v = {"id": "SC001", "resource": "PersistentVolumeClaim/x",
         "found": "local-path", "expected": "managed-csi"}
    out = augment_explanation(v)
    assert out == ""
