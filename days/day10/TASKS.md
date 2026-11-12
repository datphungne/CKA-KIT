# Day 10 — Timed Mock Exam A — 100 Points

**Initialize:** From the kit root, `bash days/day10/setup.sh`. **Score:** `bash days/day10/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d10` unless the task explicitly says otherwise.

> **Mock rule:** Complete all five sections within **120 minutes**. Each section carries the points shown in its title. Automated verification is partial and is **not** the official CKA scoring system.

## Exercise 10.1 — Cluster admin [25 pts] (25 min)

**Your mission:** Without harming your cluster, record etcd static Pod location, kubelet version, and a **validated etcd snapshot** on a disposable control plane. Save notes `answers/day10-admin.txt`.

**Pass when:** Snapshot exists; report accurately documents node/control-plane state.

**Check yourself:**

```bash
Manual inspect: admin/VM-TRACK.md
```

## Exercise 10.2 — Networking [20 pts] (25 min)

**Your mission:** Fix `backend-svc` selector. Create Service `bad-image-svc` for `bad-image` Deployment after repairing its image. Configure NetworkPolicy `trusted-only` selecting `app=backend`, permitting only Pods `role=trusted` on TCP/80.

**Pass when:** Endpoints Ready and traffic allowed/denied as specified.

**Check yourself:**

```bash
kubectl -n cka-d10 get svc,netpol
```

## Exercise 10.3 — Workloads [15 pts] (20 min)

**Your mission:** Create `mock-web` Deployment, 3 replicas, `nginx:1.27`, readiness HTTP `/:80`, ConfigMap `mock-config` setting `MODE=test`, exposed as env var `MODE`.

**Pass when:** 3/3 Ready, probe and env correctly configured.

**Check yourself:**

```bash
kubectl -n cka-d10 get deploy mock-web -o yaml
```

## Exercise 10.4 — RBAC / maintenance [25 pts] (25 min)

**Your mission:** Create SA `mock-viewer`, Role `mock-reader` get/list/watch Pods, binding `mock-reader-binding`; safely cordon/drain/uncordon a worker and record in `answers/day10-maintenance.txt`.

**Pass when:** RBAC limited to read Pods; all nodes schedulable.

**Check yourself:**

```bash
kubectl auth can-i list pods --as=system:serviceaccount:cka-d10:mock-viewer -n cka-d10
```

## Exercise 10.5 — Storage [15 pts] (25 min)

**Your mission:** Create PVC `mock-data` 1Gi via dynamic provisioner; Pod `mock-writer` using `busybox:1.36` mounts claim at `/data`. Write `mock-10` to `/data/proof.txt`.

**Pass when:** PVC Bound, Pod Ready, data readable.

**Check yourself:**

```bash
kubectl -n cka-d10 exec mock-writer -- cat /data/proof.txt
```

## End of day

Run:

```bash
bash days/day10/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
