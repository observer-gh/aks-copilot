import yaml


def inspect_ingress_class(text: str):
    """
    SC003: Ingress must define ingressClassName or AGIC annotation.
    """
    try:
        doc = yaml.safe_load(text)
    except Exception:
        return []

    if not isinstance(doc, dict):
        return []

    if doc.get("kind") != "Ingress":
        return []

    metadata = doc.get("metadata", {})
    annos = metadata.get("annotations", {}) or {}
    spec = doc.get("spec", {}) or {}

    has_class = "ingressClassName" in spec
    has_agic = any("application-gateway" in v for v in annos.values())

    if has_class or has_agic:
        return []

    return [{
        "id": "SC003",
        "resource": doc.get("metadata", {}).get("name", "<unknown>"),
        "path": "/spec",
        "found": "no ingressClass/AGIC",
        "expected": "define ingressClassName or AGIC annotations",
        "severity": "error"
    }]
