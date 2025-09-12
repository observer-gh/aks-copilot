# Ingress on AKS (AGIC Basics)

AKS commonly uses Application Gateway Ingress Controller (AGIC) for L7 ingress with WAF and TLS.

Why it matters:

- k3s/nginx ingress annotations differ from AGIC.
- Missing/incorrect class/annotations → route failures.

Minimum checks:

- Ingress class defined (e.g., `kubernetes.io/ingress.class: azure/application-gateway`)
- Required AGIC annotations per feature (TLS, backend protocol, health probes).

Source:
https://learn.microsoft.com/azure/application-gateway/ingress-controller-overview
