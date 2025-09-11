from src.inspect.storageclass import inspect_storageclass


def test_sc001_emitted_for_local_path():
    bad_yaml = """
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mydata
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 1Gi
  storageClassName: local-path
"""
    v = inspect_storageclass(bad_yaml)
    assert len(v) == 1
    assert v[0]["id"] == "SC001"
    assert v[0]["path"] == "/spec/storageClassName"
    assert v[0]["found"] == "local-path"
    assert v[0]["expected"] == "managed-csi"


def test_no_violation_when_managed_csi():
    ok_yaml = """
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ok
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 1Gi
  storageClassName: managed-csi
"""
    v = inspect_storageclass(ok_yaml)
    assert v == []
