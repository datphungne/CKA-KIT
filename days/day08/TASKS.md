# Day 08 — Cluster Troubleshooting — Safe & Isolated

**Initialize:** From the kit root, `bash days/day08/setup.sh`. **Score:** `bash days/day08/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d08` unless the task explicitly says otherwise.

> **Admin safety:** Cluster-wide or host actions must be performed only on the dedicated `cka-14d` kind lab or separate throwaway VMs. Read `admin/VM-TRACK.md`.

## Exercise 08.1 — Service port failure (12 min)

**Your mission:** `upstream-svc` targets port 8081 but `upstream` nginx listens on 80. Find the cause via endpoints and Pod specs; repair.

**Pass when:** Internal HTTP request works on Service port 80.

**Check yourself:**

```bash
kubectl -n cka-d08 get svc upstream-svc -o yaml
```

## Exercise 08.2 — CoreDNS path (12 min)

**Your mission:** From `net-client`, resolve `dns-backend-svc.cka-d08.svc.cluster.local`, then inspect CoreDNS service, Deployment and logs. Save the observed DNS result to `answers/day08-dns.txt`.

**Pass when:** DNS resolves and CoreDNS Pods healthy.

**Check yourself:**

```bash
kubectl -n cka-d08 exec net-client -- nslookup dns-backend-svc
```

## Exercise 08.3 — Pod scheduling (12 min)

**Your mission:** Cordon one worker, add required affinity to a new Pod `pinned-app` for that worker and observe Pending. Then safely restore scheduling so the Pod can run; uncordon worker.

**Pass when:** pinned-app Ready, worker uncordoned.

**Check yourself:**

```bash
kubectl -n cka-d08 get pod pinned-app -o wide
```

## Exercise 08.4 — kubelet outage [ISOLATED ONLY] (25 min)

**Your mission:** On dedicated kind node `cka-14d-worker2`, stop kubelet via `admin/host-fault.sh kubelet stop --confirm`. Diagnose NotReady and restore via `admin/host-fault.sh kubelet restore --confirm`. This changes the **node container**, not your real host.

**Pass when:** All nodes Ready after restore.

**Check yourself:**

```bash
kubectl get nodes
```

## Exercise 08.5 — API server outage [ISOLATED ONLY] (30 min)

**Your mission:** Run `admin/host-fault.sh apiserver break --confirm` to insert an invalid API-server flag into its static Pod manifest on the dedicated kind control-plane node. Diagnose by `docker exec`/crictl, then `admin/host-fault.sh apiserver restore --confirm`.

**Pass when:** API server reachable; all nodes recover.

**Check yourself:**

```bash
kubectl get --raw /readyz
```

## End of day

Run:

```bash
bash days/day08/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
