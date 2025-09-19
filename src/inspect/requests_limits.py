from typing import List, Dict
import yaml


def _scan_containers(objs, base_path, kind=None) -> List[Dict]:
    out = []
    for i, c in enumerate(objs or []):
        res = (c or {}).get("resources") or {}
        has_req = isinstance(res.get("requests"), dict) and len(
            res.get("requests") or {}) > 0
        has_lim = isinstance(res.get("limits"), dict) and len(
            res.get("limits") or {}) > 0
        if not (has_req and has_lim):
            name = (c or {}).get("name", f"idx-{i}")
            # include desired defaults from config
            from src.config import get_config
            cfg = get_config()
            sc002 = cfg.get("sc002", {})
            desired = {
                "requests": {"cpu": sc002.get("cpu_requests"), "memory": sc002.get("mem_requests")},
                "limits": {"cpu": sc002.get("cpu_limits"), "memory": sc002.get("mem_limits")},
            }
            # normalize to the project's violation shape used by report writer
            resource_str = f"{kind}/{name}" if kind else name
            out.append({
                "id": "SC002",
                "rule_id": "SC002",
                "file": None,  # caller may fill
                "kind": kind,
                "name": name,
                "resource": resource_str,
                "path": f"{base_path}/containers/{i}/resources",
                "current": res,
                "desired": desired,
                "found": res,
                "expected": desired,
                "severity": "error",
                "message": "missing resource requests/limits",
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
            v += _scan_containers(spec.get("containers"), "/spec", kind=kind)
        elif kind in ("Deployment", "StatefulSet"):
            tpl = (((doc.get("spec") or {}).get(
                "template") or {}).get("spec") or {})
            base = "/spec/template/spec"
            v += _scan_containers(tpl.get("containers"), base, kind=kind)
        else:
            continue
    return v
