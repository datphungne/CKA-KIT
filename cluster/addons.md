# Optional addons

The default kind cluster is created with **Calico**, so network policies can be tested rather than merely applied. It has a StorageClass (check `kubectl get sc`). If you want Ingress and Gateway API exercises to actually route traffic, install compatible controllers **on this disposable cluster** following their official documentation:

- Ingress: https://kubernetes.github.io/ingress-nginx/deploy/#quick-start (verify current compatibility; this project is subject to maintenance status changes)
- Gateway API: https://gateway-api.sigs.k8s.io/guides/ (install Gateway CRDs **and** a compatible controller; CRDs alone don't route)
- Metrics Server: https://github.com/kubernetes-sigs/metrics-server (kind TLS settings may need lab-only adjustments)

Controller-dependent exercises are explicitly tagged **OPTIONAL** in TASKS.md and reported as **MANUAL** in the checker. Do not assume that a created Ingress/HTTPRoute is functional without a matching controller.
