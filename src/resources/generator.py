"""Infer required Azure resources from manifests + violations and write resources.md.

Design (FR3): Pure functions; no network calls. Ordering stable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Iterable, Tuple, Set
import yaml
import pathlib

ORDER = [
    "resourceGroup",
    "aksCluster",
    "containerRegistry",
    "ingressController",
    "publicIp",
    "storageClass",
    "persistentStorage",
    "logAnalytics",
    "monitor",
    "keyVault",
]

SECRET_THRESHOLD = 5


@dataclass
class ResourceInfo:
    id: str
    name: str
    purpose: str
    required: bool
    reason: str
    signals: List[str]

    def to_row(self) -> List[str]:
        return [self.name, self.purpose, "yes" if self.required else "no", self.reason, self._signals_compact()]

    def _signals_compact(self) -> str:
        if not self.signals:
            return ""
        if len(self.signals) <= 5:
            return ", ".join(self.signals)
        extra = len(self.signals) - 5
        return ", ".join(self.signals[:5]) + f" +{extra} more"


def _safe_load_all(text: str) -> List[dict]:
    try:
        return [d for d in yaml.safe_load_all(text) if isinstance(d, dict)]
    except Exception:
        return []


def _collect_signals(file_path: str, text: str) -> Dict[str, Set[str]]:
    """Return grouped signals extracted from a YAML file.

    Signals stored under keys: ingress, pvc, images, secrets.
    Each value is a set of canonical token strings.
    Canonical token: file.yaml:Kind/Name (omit /Name if name missing).
    """
    out = {"ingress": set(), "pvc": set(), "images": set(), "secrets": set()}
    docs = _safe_load_all(text)
    for doc in docs:
        kind = doc.get("kind")
        meta = doc.get("metadata") or {}
        name = meta.get("name")
        token = f"{pathlib.Path(file_path).name}:{kind}{'/' + name if name else ''}" if kind else pathlib.Path(
            file_path).name
        if kind == "Ingress":
            out["ingress"].add(token)
        if kind == "PersistentVolumeClaim":
            out["pvc"].add(token)
        # container images
        pod_specs = []
        if kind == "Pod":
            pod_specs.append(doc.get("spec") or {})
        elif kind in ("Deployment", "StatefulSet"):
            spec = (((doc.get("spec") or {}).get(
                "template") or {}).get("spec") or {})
            pod_specs.append(spec)
        for ps in pod_specs:
            for c in (ps.get("containers") or []):
                img = (c or {}).get("image")
                if not isinstance(img, str):
                    continue
                host = img.split("/", 1)[0] if "/" in img else "docker.io"
                out["images"].add(host)
            # secret refs: envFrom.secretRef.name, env.valueFrom.secretKeyRef.name, volumes[].secret.secretName
            for c in (ps.get("containers") or []):
                env_from = c.get("envFrom") or []
                for ef in env_from:
                    sec = (ef or {}).get("secretRef") or {}
                    n = sec.get("name")
                    if n:
                        out["secrets"].add(n)
                for env in (c.get("env") or []):
                    vfrom = (env or {}).get("valueFrom") or {}
                    sk = (vfrom.get("secretKeyRef") or {}).get("name")
                    if sk:
                        out["secrets"].add(sk)
            for vol in (ps.get("volumes") or []):
                secv = (vol or {}).get("secret") or {}
                n = secv.get("secretName") or secv.get("name")
                if n:
                    out["secrets"].add(n)
    return out


def infer_resources(violations: List[Dict], file_texts: Dict[str, str]) -> Tuple[List[ResourceInfo], List[str]]:
    """Infer resources and return (resources, all_signal_tokens)."""
    # aggregate signals
    agg = {"ingress": set(), "pvc": set(), "images": set(), "secrets": set()}
    for fp, text in file_texts.items():
        local = _collect_signals(fp, text)
        for k, v in local.items():
            agg[k].update(v)

    # violation based triggers
    has_sc001 = any(v.get("id") == "SC001" for v in violations)

    resources: List[ResourceInfo] = []

    def add(rid: str, name: str, purpose: str, required: bool, reason: str, signals: Iterable[str]):
        resources.append(ResourceInfo(rid, name, purpose,
                         required, reason, sorted(set(signals))))

    # Baseline always
    add("resourceGroup", "Resource Group", "Logical container",
        True, "Required for all Azure resources", [])
    add("aksCluster", "AKS Cluster", "Run workloads", True, "Target platform", [])
    add("logAnalytics", "Log Analytics Workspace", "Centralized logging/metrics",
        True, "Provide cluster + workload insights", [])
    add("monitor", "Azure Monitor Integration",
        "Metrics/alerts pipeline", True, "Observability baseline", [])

    # container registry: any non public host
    private_hosts = [h for h in agg["images"]
                     if h not in {"docker.io", "mcr.microsoft.com"}]
    if private_hosts:
        add("containerRegistry", "Container Registry (ACR)", "Store container images", True,
            "Private/enterprise image hosting detected", private_hosts)

    if agg["ingress"]:
        add("ingressController", "Ingress Controller", "HTTP(S) routing",
            True, "Ingress objects present", agg["ingress"])
        add("publicIp", "Public IP", "Expose ingress externally", True,
            "Needed for external ingress endpoint", agg["ingress"])

    # storageClass + persistent storage
    if has_sc001 or agg["pvc"]:
        if has_sc001:
            add("storageClass", "Storage Class (Managed)", "Persistent storage", True,
                "Storage normalization required", [s for s in agg["pvc"]])
        if agg["pvc"]:
            add("persistentStorage", "Persistent Volume (Managed Disk / Azure Files)", "Stateful workload storage", True,
                "PVC detected", agg["pvc"])

    if len(agg["secrets"]) >= SECRET_THRESHOLD or private_hosts:
        add("keyVault", "Key Vault", "Secret management", True, "Secure secret lifecycle recommended",
            agg["secrets"])  # may be empty if only private image triggered

    # stable order filter
    order_index = {rid: i for i, rid in enumerate(ORDER)}
    resources.sort(key=lambda r: order_index.get(r.id, 999))
    all_signal_tokens = sorted(
        {*agg["ingress"], *agg["pvc"], *agg["images"], *agg["secrets"]})
    return resources, all_signal_tokens


def write_resources_md(resources: List[ResourceInfo], signals: List[str], path: str = "resources.md") -> None:
    lines = ["# Required Azure Resources", "",
             "This file lists inferred Azure resources based on manifests and detected violations.", ""]
    # table header
    lines.append("| Resource | Purpose | Required | Reason | Signals |")
    lines.append("| -------- | ------- | -------- | ------ | ------- |")
    for r in resources:
        lines.append(
            f"| {r.name} | {r.purpose} | {'yes' if r.required else 'no'} | {r.reason} | {r._signals_compact()} |")
    lines.append("")
    lines.append("## Detected Signals")
    if not signals:
        lines.append("- (none)")
    else:
        for s in signals:
            lines.append(f"- {s}")
    pathlib.Path(path).write_text("\n".join(lines), encoding="utf-8")


__all__ = ["infer_resources", "write_resources_md", "ResourceInfo"]
