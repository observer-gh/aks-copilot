import json
from src.patch.generator import build_patch_ops, write_patch_json
from src.patch.dryrun import dry_run_validate


def test_build_patch_ops_and_write(tmp_path):
    v = [
        {
            "rule_id": "SC001",
            "file": "tests/fixtures/pvc_bad.yml",
            "kind": "PersistentVolumeClaim",
            "name": "data-myapp-0",
            "path": "/spec/storageClassName",
            "current": "local-path",
            "desired": "standard",
        }
    ]
    patches = build_patch_ops(v)
    assert isinstance(patches, list)
    assert len(patches) == 1
    assert patches[0]["file"].endswith("pvc_bad.yml")
    assert patches[0]["ops"][0]["op"] == "replace"
    out = tmp_path / "patch.json"
    write_patch_json(patches, str(out))
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == patches


def test_dry_run_validate_success(tmp_path):
    # use fixture file path
    v = [
        {
            "rule_id": "SC001",
            "file": "tests/fixtures/pvc_bad.yml",
            "path": "/spec/storageClassName",
            "desired": "standard",
        }
    ]
    patches = build_patch_ops(v)
    results = dry_run_validate(patches, manifests_root=None, strict=False)
    assert isinstance(results, list)
    assert results[0]["success"] is True
