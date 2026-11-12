# Day 03 — Services, DNS & NetworkPolicies

**Initialize:** From the kit root, `bash days/day03/setup.sh`. **Score:** `bash days/day03/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d03` unless the task explicitly says otherwise.

## Exercise 03.1 — ClusterIP (10 min)

**Your mission:** `api` Deployment (3 nginx replicas) exists. Create `api-svc` ClusterIP Service with port 8080 → targetPort 80 and selector `app=api`.

**Pass when:** Service has three ready endpoints; in-cluster curl returns HTTP 200.

**Check yourself:**

```bash
kubectl -n cka-d03 get endpointslice -l kubernetes.io/service-name=api-svc
```

## Exercise 03.2 — NodePort (10 min)

**Your mission:** Expose existing `frontend` Deployment with a `frontend-nodeport` Service on NodePort **30080**, service port 80 and target port 80. From host, test `curl http://127.0.0.1:30080` (requires kind worker port mapping).

**Pass when:** HTTP succeeds via mapped NodePort.

**Check yourself:**

```bash
kubectl -n cka-d03 get svc frontend-nodeport
```

## Exercise 03.3 — Cluster DNS (10 min)

**Your mission:** Create Service `database` targeting the seeded `database` Deployment, port 80. From `dns-client`, resolve `database.cka-d03.svc.cluster.local` and write output into `answers/day03-dns.txt`.

**Pass when:** FQDN resolves; file records the query result.

**Check yourself:**

```bash
kubectl -n cka-d03 exec dns-client -- nslookup database.cka-d03.svc.cluster.local
```

## Exercise 03.4 — Enforced network policy (20 min)

**Your mission:** Apply NetworkPolicy `database-ingress` selecting `app=database`. Allow TCP/80 ingress only from Pods labeled `role=frontend` in this namespace (`trusted` is allowed, `outsider` must be denied). Default deny applies to that selected backend.

**Pass when:** Curl from trusted succeeds; outsider fails/times out. Calico must be healthy.

**Check yourself:**

```bash
kubectl -n cka-d03 get networkpolicy database-ingress -o yaml
```

## Exercise 03.5 — Ingress and Gateway API [OPTIONAL] (20 min)

**Your mission:** With an installed Ingress controller, create Ingress `api-ingress` routing host `cka.local` and path `/` to `api-svc` port 8080. With Gateway API CRDs **and** controller, create `api-route` HTTPRoute targeting `api-svc`, and attach it to a compatible Gateway.

**Pass when:** Verify actual HTTP routing through the controllers, not just object creation.

**Check yourself:**

```bash
kubectl -n cka-d03 get ingress,httproute 2>/dev/null || true
```

## End of day

Run:

```bash
bash days/day03/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
