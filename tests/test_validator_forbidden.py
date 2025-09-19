from src.patch.validator import validate_patch_ops


def test_validate_patch_ops_forbidden_path():
    ok, msg = validate_patch_ops([
        {"op": "add", "path": "/metadata/uid", "value": "abc"}
    ])
    assert not ok
    assert "forbidden" in msg

    ok2, msg2 = validate_patch_ops([
        {"op": "add", "path": "/spec/replicas", "value": 3}
    ])
    assert ok2
    assert msg2 == ""


def test_validate_patch_ops_too_many_ops():
    ops = [{"op": "add", "path": f"/spec/x{i}", "value": i}
           for i in range(0, 11)]
    ok, msg = validate_patch_ops(ops)
    assert not ok
    assert "too many ops" in msg
