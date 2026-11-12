# Day 18 — Advanced Networking: Default Deny, Egress, Namespaces, Endpoints [TOPIC LAB]

**Initialize:** From the kit root, `bash days/day18/setup.sh`. **Score:** `bash days/day18/verify.sh`.

**Workspace:** All Kubernetes resources go to namespace `cka-d18` unless the task explicitly says otherwise. Setup also creates namespace `cka-d18-frontend` (label `team=frontend`) with Pod `fe-client`. In `cka-d18` you have Deployments/Services `web` and `api`, plus Pods `client` (`role=client`) and `other-client`. Do the exercises in order.

## Exercise 18.1 — Default deny with DNS allowed (15 min)

**Your mission:** Create NetworkPolicy `default-deny` that denies **all ingress and egress** for every Pod in `cka-d18`. Then create `allow-dns` so every Pod may still send DNS queries (UDP and TCP 53) to the CoreDNS Pods in `kube-system`.

**Pass when:** `client` can no longer reach `web`, but name resolution still works.

**Check yourself:**

```bash
kubectl -n cka-d18 exec client -- nslookup web; kubectl -n cka-d18 exec client -- wget -T 3 -qO- web
```

## Exercise 18.2 — Egress and ingress for one flow (15 min)

**Your mission:** Allow exactly one flow: Pods `role=client` → Pods `app=api` on TCP/80. You need an egress rule on the client side (`client-egress`) **and** an ingress rule on the server side (`api-ingress`).

**Pass when:** `client` reaches `api`; `client` still cannot reach `web`; `other-client` cannot reach `api`.

**Check yourself:**

```bash
kubectl -n cka-d18 exec client -- wget -T 3 -qO- api
```

## Exercise 18.3 — Traffic from another namespace (12 min)

**Your mission:** Create NetworkPolicy `web-from-frontend` that lets Pods from any namespace labeled `team=frontend` reach `app=web` on TCP/80.

**Pass when:** `fe-client` in `cka-d18-frontend` reaches `web.cka-d18`; `client` in `cka-d18` still cannot.

**Check yourself:**

```bash
kubectl -n cka-d18-frontend exec fe-client -- wget -T 3 -qO- web.cka-d18
```

## Exercise 18.4 — ExternalName Service (8 min)

**Your mission:** Create Service `legacy-db` of type `ExternalName` that aliases `api.cka-d18.svc.cluster.local`.

**Pass when:** `legacy-db` resolves (as a CNAME) from `client`.

**Check yourself:**

```bash
kubectl -n cka-d18 exec client -- nslookup legacy-db
```

## Exercise 18.5 — Service without selector + manual EndpointSlice (15 min)

**Your mission:** Create Service `manual-svc` (port 80, **no selector**) and an EndpointSlice `manual-svc-1` that points it at the current IP of the `api` Pod on port 80.

**Pass when:** `manual-svc` has a ready endpoint and `client` gets an HTTP response through it.

**Check yourself:**

```bash
kubectl -n cka-d18 get endpointslice -l kubernetes.io/service-name=manual-svc
```

## End of day

Run:

```bash
bash days/day18/verify.sh
```
