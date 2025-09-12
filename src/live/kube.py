import json
from typing import Set, List, Dict
from src.live.shell import run


def list_storage_classes() -> Set[str]:
    code, out, err = run("kubectl get storageclass -o json", timeout=5)
    if code != 0 or not out:
        return set()
    data = json.loads(out)
    items: List[Dict] = data.get("items", [])
    return {i.get("metadata", {}).get("name", "") for i in items if i.get("metadata")}
