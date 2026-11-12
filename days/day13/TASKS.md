# Day 13 — Final Speed Drills

**Initialize:** From the kit root, `bash days/day13/setup.sh`. **Score:** `bash days/day13/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d13` unless the task explicitly says otherwise.

## Exercise 13.1 — kubectl sprint (10 min)

**Your mission:** Create `alpha`, `beta` Pods with nginx:1.27. Create Deployments `rapid-a` (2 replicas) and `rapid-b` (3 replicas), nginx:1.27.

**Pass when:** All ready; correct replica counts.

**Check yourself:**

```bash
kubectl -n cka-d13 get pods,deploy
```

## Exercise 13.2 — Networking sprint (12 min)

**Your mission:** Repair `gateway-svc` selector to `app=gateway`. Create NetworkPolicy `gateway-allow` allowing traffic to gateway Pods on 80 from Pods `role=tester` only (create/label client as needed).

**Pass when:** Service endpoints Ready; policy selects correct backend.

**Check yourself:**

```bash
kubectl -n cka-d13 get svc,netpol
```

## Exercise 13.3 — Storage sprint (12 min)

**Your mission:** Create 500Mi PVC `speed-data` using a working StorageClass. Mount to `speed-writer` Pod at `/data`.

**Pass when:** Claim Bound, Pod Ready.

**Check yourself:**

```bash
kubectl -n cka-d13 get pvc speed-data
```

## Exercise 13.4 — RBAC sprint (12 min)

**Your mission:** Create SA `speed-auditor`, Role `speed-reader` read-only ConfigMap access, and binding `speed-binding`.

**Pass when:** SA allowed list ConfigMaps and denied delete.

**Check yourself:**

```bash
kubectl auth can-i list configmaps --as=system:serviceaccount:cka-d13:speed-auditor -n cka-d13
```

## Exercise 13.5 — Emergency repair (12 min)

**Your mission:** Fix seeded `broken-rollout` Deployment bad image, then verify nginx is Ready.

**Pass when:** Rollout succeeds.

**Check yourself:**

```bash
kubectl -n cka-d13 rollout status deploy/broken-rollout
```

## End of day

Run:

```bash
bash days/day13/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
