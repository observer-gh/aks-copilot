from pathlib import Path
import json
from typer.testing import CliRunner
from src.cli.main import app


def _prep(tmp_path):
    # minimal config to avoid real LLM use
    (tmp_path / "config.json").write_text(json.dumps({"llm": "stub"}))


def _run_fix(tmp_path, files):
    runner = CliRunner()
    result = runner.invoke(app, ["fix-tree", str(tmp_path)]) if len(
        files) > 1 else runner.invoke(app, ["fix", str(files[0])])
    assert result.exit_code == 0, result.stdout
    rfile = Path("resources.md")
    assert rfile.exists(), "resources.md should be created"
    return rfile.read_text(encoding="utf-8")


def test_resources_pvc_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _prep(tmp_path)
    pvc = tmp_path / "pvc.yml"
    pvc.write_text("""
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 1Gi
  storageClassName: local-path
"""
                   )
    text = _run_fix(tmp_path, [pvc])
    # Expect storageClass + persistentStorage rows plus baselines
    assert "Storage Class (Managed)" in text
    assert "Persistent Volume (Managed Disk / Azure Files)" in text


def test_resources_private_image(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _prep(tmp_path)
    dep = tmp_path / "deploy.yml"
    dep.write_text("""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  selector: { matchLabels: { app: web } }
  template:
    metadata: { labels: { app: web } }
    spec:
      containers:
      - name: app
        image: mycorp.azurecr.io/app:1.0
"""
                   )
    text = _run_fix(tmp_path, [dep])
    assert "Container Registry (ACR)" in text


def test_resources_many_secrets_keyvault(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _prep(tmp_path)
    pod = tmp_path / "pod.yml"
    # create 6 distinct secrets to cross threshold
    envs = "\n".join(
        [f"        - name: VAR{i}\n          valueFrom:\n            secretKeyRef:\n              name: secret{i}\n              key: k" for i in range(6)])
    pod.write_text(f"""
apiVersion: v1
kind: Pod
metadata:
  name: demo
spec:
  containers:
  - name: c
    image: nginx
    env:
{envs}
"""
                   )
    text = _run_fix(tmp_path, [pod])
    assert "Key Vault" in text


def test_resources_signals_truncation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _prep(tmp_path)
    # create >5 PVCs to exceed compact list limit
    for i in range(7):
        (tmp_path / f"pvc{i}.yml").write_text(f"""
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data{i}
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 1Gi
  storageClassName: local-path
"""
                                              )
    # run tree so all files collected
    text = _run_fix(tmp_path, list(tmp_path.glob("pvc*.yml")))
    # expect '+N more' pattern
    import re
    assert re.search(
        r"\+\d+ more", text), "Expected '+N more' pattern in output"


def test_resources_empty_only_baseline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _prep(tmp_path)
    # empty file (no manifests) => only baseline rows
    f = tmp_path / "empty.yml"
    f.write_text("# nothing")
    text = _run_fix(tmp_path, [f])
    assert "Resource Group" in text and "AKS Cluster" in text
    # no optional ones
    assert "Ingress Controller" not in text
    assert "Container Registry (ACR)" not in text


def test_resources_ingress(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _prep(tmp_path)
    ingress = tmp_path / "ing.yml"
    ingress.write_text("""
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: demo
spec:
  rules: []
"""
                       )
    text = _run_fix(tmp_path, [ingress])
    assert "Ingress Controller" in text
    assert "Public IP" in text


def test_resources_multidoc_aggregation(tmp_path, monkeypatch):
    """Single file containing Ingress + PVC should trigger both ingress + storage related resources."""
    monkeypatch.chdir(tmp_path)
    _prep(tmp_path)
    multi = tmp_path / "combo.yml"
    multi.write_text(
        """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: demo
spec:
  rules: []
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: datax
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 1Gi
  storageClassName: local-path
"""
    )
    text = _run_fix(tmp_path, [multi])
    assert "Ingress Controller" in text
    assert "Public IP" in text
    assert "Persistent Volume (Managed Disk / Azure Files)" in text
    assert "Storage Class (Managed)" in text
