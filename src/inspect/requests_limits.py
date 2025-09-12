from typing import List, Dict
import yaml


def _scan_containers(objs, base_path) -> List[Dict]:
    out = []
    for i, c in enumerate(objs or []):
        res = (c or {}).get("resources") or {}
        has_req = isinstance(res.get("requests"), dict) and len(
            res.get("requests") or {}) > 0
        has_lim = isinstance(res.get("limits"), dict) and len(
            res.get("limits") or {}) > 0
        if not (has_req and has_lim):
            name = (c or {}).get("name", f"idx-{i}")
            out.append({
                "id": "SC002",
                "resource": f"container/{name}",
                "path": f"{base_path}/containers/{i}/resources",
                "found": "missing requests/limits",
                "expected": "define cpu/memory requests and limits",
                "severity": "error",
                "rule": "resources.requests_limits",
            })
    return out


def inspect_requests_limits(manifest_yaml: str) -> List[Dict]:
    """
    Detect containers missing resources.requests or resources.limits.
    Targets: Pod, Deployment, StatefulSet (MVP).
    """
    v: List[Dict] = []
    try:
        docs = list(yaml.safe_load_all(manifest_yaml))
    except Exception:
        return v

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        kind = doc.get("kind")
        if kind == "Pod":
            spec = (doc.get("spec") or {})
            v += _scan_containers(spec.get("containers"), "/spec")
        elif kind in ("Deployment", "StatefulSet"):
            tpl = (((doc.get("spec") or {}).get(
                "template") or {}).get("spec") or {})
            base = "/spec/template/spec"
            v += _scan_containers(tpl.get("containers"), base)
        else:
            continue
    return v
