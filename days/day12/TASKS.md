# Day 12 — Timed Mock Exam B — 100 Points

**Initialize:** From the kit root, `bash days/day12/setup.sh`. **Score:** `bash days/day12/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d12` unless the task explicitly says otherwise.

> **Admin safety:** Cluster-wide or host actions must be performed only on the dedicated `cka-14d` kind lab or separate throwaway VMs. Read `admin/VM-TRACK.md`.

> **Mock rule:** Complete all five sections within **120 minutes**. Each section carries the points shown in its title. Automated verification is partial and is **not** the official CKA scoring system.

## Exercise 12.1 — Cluster ops [25 pts] (25 min)

**Your mission:** Record kubeadm version, take snapshot of etcd in disposable lab, then cordon/drain/uncordon one worker. Write `answers/day12-admin.txt`.

**Pass when:** Snapshot verified; worker Ready and schedulable.

**Check yourself:**

```bash
Manual snapshot check + kubectl get nodes
```

## Exercise 12.2 — Troubleshooting [30 pts] (30 min)

**Your mission:** Fix `faulty-image` invalid nginx tag and `payments-svc` wrong selector. Identify one simulated node failure by using `admin/host-fault.sh kubelet` on worker2, then restore.

**Pass when:** Deployments Ready, Service endpoints present, all nodes Ready.

**Check yourself:**

```bash
kubectl -n cka-d12 get deploy,svc
```

## Exercise 12.3 — Networking [20 pts] (25 min)

**Your mission:** Create NodePort Service `payments-nodeport` for `payments` with nodePort 30080 and service port 80. Create policy `payments-allow` selecting `app=payments` and allow only `role=allowed` TCP/80.

**Pass when:** NodePort works; policy restricts unauthorized clients.

**Check yourself:**

```bash
kubectl -n cka-d12 get svc,netpol
```

## Exercise 12.4 — Workloads [15 pts] (20 min)

**Your mission:** Create DaemonSet `log-agent` with `busybox:1.36` sleep; CronJob `daily-job` scheduled `*/5 * * * *` with busybox echo; ConfigMap `runtime-settings` MODE=test.

**Pass when:** DaemonSet available on schedulable worker nodes; CronJob and ConfigMap valid.

**Check yourself:**

```bash
kubectl -n cka-d12 get ds,cj,configmap
```

## Exercise 12.5 — Storage [10 pts] (20 min)

**Your mission:** Create `backup-claim` PVC 1Gi dynamic StorageClass and Pod `backup-pod` mounting claim at `/backup`.

**Pass when:** PVC Bound, Pod Ready with mount.

**Check yourself:**

```bash
kubectl -n cka-d12 get pvc backup-claim
```

## End of day

Run:

```bash
bash days/day12/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
