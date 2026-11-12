# Day 14 — Final Mock Exam — 100 Points

**Initialize:** From the kit root, `bash days/day14/setup.sh`. **Score:** `bash days/day14/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d14` unless the task explicitly says otherwise.

> **Admin safety:** Cluster-wide or host actions must be performed only on the dedicated `cka-14d` kind lab or separate throwaway VMs. Read `admin/VM-TRACK.md`.

> **Mock rule:** Complete all five sections within **120 minutes**. Each section carries the points shown in its title. Automated verification is partial and is **not** the official CKA scoring system.

## Exercise 14.1 — Cluster [25 pts] (25 min)

**Your mission:** Take an etcd snapshot on isolated kind CP, record control-plane static Pod path and kubelet service status in `answers/day14-admin.txt`. **Do not restore over live etcd.**

**Pass when:** Validated snapshot and correct observed cluster state.

**Check yourself:**

```bash
Manual snapshot evidence + node Ready
```

## Exercise 14.2 — Troubleshooting [30 pts] (30 min)

**Your mission:** Fix seeded `billing` Deployment bad image and `orders-svc` bad selector; additionally inspect kubelet logs inside worker2 and summarize in `answers/day14-troubleshooting.txt`.

**Pass when:** Both Deployments healthy and Service endpoints Ready.

**Check yourself:**

```bash
kubectl -n cka-d14 get deploy,svc
```

## Exercise 14.3 — Networking [20 pts] (25 min)

**Your mission:** Create ClusterIP `billing-svc` port 8080→80 to billing. Apply NetworkPolicy `orders-allow` selecting `app=orders`, allow TCP/80 only from Pods labeled `role=trusted`.

**Pass when:** Service usable; trusted client allowed, untrusted blocked.

**Check yourself:**

```bash
kubectl -n cka-d14 get svc,netpol
```

## Exercise 14.4 — Workloads [15 pts] (20 min)

**Your mission:** Create Deployment `final-web`, 3 replicas, nginx:1.27, rollingUpdate maxUnavailable=1; Secret `final-secret` TOKEN=pass; mount it as environment variable TOKEN; readiness probe `/` port 80.

**Pass when:** 3/3 Ready with correct rollout, env and readiness.

**Check yourself:**

```bash
kubectl -n cka-d14 get deploy final-web -o yaml
```

## Exercise 14.5 — Storage [10 pts] (20 min)

**Your mission:** Create `final-claim` PVC 1Gi dynamic StorageClass, Pod `final-writer` mounts `/data`; write `cka-final` in `/data/proof.txt` and verify it.

**Pass when:** PVC Bound; proof readable from running container.

**Check yourself:**

```bash
kubectl -n cka-d14 exec final-writer -- cat /data/proof.txt
```

## End of day

Run:

```bash
bash days/day14/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
