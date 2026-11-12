# Day 04 — Persistent Volumes and Claims

**Initialize:** From the kit root, `bash days/day04/setup.sh`. **Score:** `bash days/day04/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d04` unless the task explicitly says otherwise.

## Exercise 04.1 — Static local PV / PVC (20 min)

**Your mission:** Setup creates directory `/var/local/cka-d04` inside kind node `cka-14d-worker`. Create local PV `cka-d04-local-pv`, `1Gi`, access `ReadWriteOnce`, reclaim `Retain`, StorageClass `manual`, with nodeAffinity to `kubernetes.io/hostname=cka-14d-worker`. Then create PVC `data-claim` in `cka-d04`, request `500Mi`, class `manual`, volumeName `cka-d04-local-pv`.

**Pass when:** PVC `Bound` to the correct PV.

**Check yourself:**

```bash
kubectl -n cka-d04 get pvc data-claim
```

## Exercise 04.2 — Persistence after recreation (15 min)

**Your mission:** Create Pod `data-writer`, image `busybox:1.36`, mounting `data-claim` at `/data` and sleeping. Write `hello-cka` into `/data/proof.txt`. Delete and re-create Pod `data-writer` (do not delete PVC).

**Pass when:** The file can be read after Pod recreation.

**Check yourself:**

```bash
kubectl -n cka-d04 exec data-writer -- cat /data/proof.txt
```

## Exercise 04.3 — Dynamic provisioning (15 min)

**Your mission:** Find an existing working StorageClass (kind often provides `standard`). Create PVC `dynamic-claim` for 1Gi with that class, then mount it at `/data` to a Pod named `dynamic-reader`. If no provisioner exists, mark this task as blocked and install one in your lab.

**Pass when:** Dynamic PVC Bound and mounted.

**Check yourself:**

```bash
kubectl -n cka-d04 get pvc dynamic-claim
```

## Exercise 04.4 — Inspect access modes (8 min)

**Your mission:** Create `mode-claim` of 200Mi, `ReadWriteOnce`, `Filesystem`, using a dynamic StorageClass. Describe it and inspect its resulting PV.

**Pass when:** PVC has requested access mode and volume mode.

**Check yourself:**

```bash
kubectl -n cka-d04 get pvc mode-claim -o yaml
```

## Exercise 04.5 — Reclaim policy (12 min)

**Your mission:** Confirm `cka-d04-local-pv` uses `Retain`. Delete `data-writer` and `data-claim`; examine PV state and retained data on node. Write observations to `answers/day04-reclaim.txt`.

**Pass when:** PV becomes Released (or remains safe during deletion), file still exists on node.

**Check yourself:**

```bash
kubectl get pv cka-d04-local-pv
```

## End of day

Run:

```bash
bash days/day04/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
