import json
import pathlib

_DEFAULT = {
    "defaultSC": "managed-csi",
    "sc002": {
        "cpu_requests": "100m", "mem_requests": "128Mi",
        "cpu_limits": "200m",  "mem_limits": "256Mi"
    },
    "llm": "stub",
}

_cfg = None


def get_config() -> dict:
    global _cfg
    if _cfg is not None:
        return _cfg
    p = pathlib.Path("config.json")
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            # shallow merge
            cfg = {**_DEFAULT, **data}
            if "sc002" in data:
                cfg["sc002"] = {**_DEFAULT["sc002"], **data["sc002"]}
            _cfg = cfg
            return _cfg
        except Exception:
            _cfg = _DEFAULT
            return _cfg
    _cfg = _DEFAULT
    return _cfg
