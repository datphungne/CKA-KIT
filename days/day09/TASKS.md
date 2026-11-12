# Day 09 — Mixed Speed Challenge

**Initialize:** From the kit root, `bash days/day09/setup.sh`. **Score:** `bash days/day09/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d09` unless the task explicitly says otherwise.

## Exercise 09.1 — Deployment rollout (8 min)

**Your mission:** Create `payments` Deployment, 4 replicas, `nginx:1.27`, RollingUpdate with maxUnavailable=1 and maxSurge=1.

**Pass when:** 4/4 Ready and specified strategy.

**Check yourself:**

```bash
kubectl -n cka-d09 get deploy payments -o yaml
```

## Exercise 09.2 — RBAC under time (10 min)

**Your mission:** Create ServiceAccount `viewer`, Role `config-reader` to get/list ConfigMaps and RoleBinding `viewer-config` in `cka-d09`.

**Pass when:** SA can list ConfigMaps but not Secrets.

**Check yourself:**

```bash
kubectl auth can-i list configmaps --as=system:serviceaccount:cka-d09:viewer -n cka-d09
```

## Exercise 09.3 — NetworkPolicy under time (12 min)

**Your mission:** Apply policy `db-allow-api` to Pods `app=db` in `cka-d09`: allow ingress TCP/80 only from Pods labeled `role=api`.

**Pass when:** Role-client allowed; random-client blocked.

**Check yourself:**

```bash
kubectl -n cka-d09 get netpol db-allow-api -o yaml
```

## Exercise 09.4 — Dynamic PVC (12 min)

**Your mission:** Create `payments-data` PVC for 2Gi using a working StorageClass. Mount to Pod `payments-writer` at `/var/lib/data`.

**Pass when:** PVC Bound and Pod Ready with mount.

**Check yourself:**

```bash
kubectl -n cka-d09 get pvc payments-data
```

## Exercise 09.5 — Broken Service (10 min)

**Your mission:** `bad-svc` was deliberately created with selector `app=missing`. Repair to expose seeded `api` Deployment.

**Pass when:** Service has ready endpoints.

**Check yourself:**

```bash
kubectl -n cka-d09 get endpointslice -l kubernetes.io/service-name=bad-svc
```

## End of day

Run:

```bash
bash days/day09/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
