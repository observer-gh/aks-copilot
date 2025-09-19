from src.inspect.requests_limits import inspect_requests_limits


def test_inspector_emits_violation_for_missing_resources():
    yaml = open("tests/fixtures/deployment_no_limits.yml").read()
    v = inspect_requests_limits(yaml)
    assert isinstance(v, list)
    assert len(v) >= 1
    # ensure desired present
    assert v[0].get("desired") is not None
