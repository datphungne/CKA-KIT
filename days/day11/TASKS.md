# Day 11 — Advanced Troubleshooting

**Initialize:** From the kit root, `bash days/day11/setup.sh`. **Score:** `bash days/day11/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d11` unless the task explicitly says otherwise.

> **Admin safety:** Cluster-wide or host actions must be performed only on the dedicated `cka-14d` kind lab or separate throwaway VMs. Read `admin/VM-TRACK.md`.

## Exercise 11.1 — OOMKilled (15 min)

**Your mission:** `memory-hog` consumes 256Mi with 32Mi memory limit. Repair without removing memory limit entirely: set limit to **512Mi** and recreate Pod.

**Pass when:** Pod Running and not OOMKilled.

**Check yourself:**

```bash
kubectl -n cka-d11 describe pod memory-hog
```

## Exercise 11.2 — Readiness failure (12 min)

**Your mission:** Fix `probe-failure` HTTP readiness port 8088 to match nginx.

**Pass when:** Deployment 2/2 Ready.

**Check yourself:**

```bash
kubectl -n cka-d11 rollout status deploy/probe-failure
```

## Exercise 11.3 — Service targetPort (12 min)

**Your mission:** `web-svc` targets incorrect port 8082. Fix to port 80; use `diagnostics-client` for HTTP verification.

**Pass when:** Service returns HTTP 200.

**Check yourself:**

```bash
kubectl -n cka-d11 get svc web-svc
```

## Exercise 11.4 — Faulty kubeconfig [LOCAL] (15 min)

**Your mission:** Export current **lab** kubeconfig to `answers/day11-kubeconfig.yaml`. In a **copy only**, change server address to wrong endpoint; diagnose and fix the copy. Do not overwrite `~/.kube/config`.

**Pass when:** Corrected copy connects using `KUBECONFIG=... kubectl cluster-info`.

**Check yourself:**

```bash
Manual command on copied kubeconfig
```

## Exercise 11.5 — Scheduler interruption [ISOLATED ONLY] (30 min)

**Your mission:** Break `kube-scheduler` static Pod using `admin/host-fault.sh scheduler break --confirm` on kind CP. Inspect logs with Docker/crictl. Restore and verify scheduler recovery.

**Pass when:** `kube-system/kube-scheduler` Running after restore; new Pods can schedule.

**Check yourself:**

```bash
kubectl -n kube-system get pods -l component=kube-scheduler
```

## End of day

Run:

```bash
bash days/day11/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
