# Container Requests & Limits (Scheduling & QoS)

Kubernetes schedules pods based on `resources.requests`. Without them, placement and autoscaling are unstable.

Why it matters:

- HPA/Cluster Autoscaler rely on requests.
- QoS classes (Guaranteed/Burstable/BestEffort) depend on requests/limits.

Recommended defaults (starter):

- requests: cpu 100m, memory 128Mi
- limits: cpu 200m, memory 256Mi

Source:
https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
