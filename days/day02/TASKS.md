# Day 02 — Workloads & Scheduling

**Initialize:** From the kit root, `bash days/day02/setup.sh`. **Score:** `bash days/day02/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d02` unless the task explicitly says otherwise.

## Exercise 02.1 — Rollout / rollback (12 min)

**Your mission:** The `store` Deployment already has 4 replicas on `nginx:1.26`. Roll it to `nginx:1.27`, confirm success, then roll back. Preserve 4 replicas.

**Pass when:** Final image `nginx:1.26`, 4 ready replicas; rollout history shows revisions.

**Check yourself:**

```bash
kubectl -n cka-d02 rollout history deploy/store
```

## Exercise 02.2 — ConfigMaps & Secrets (12 min)

**Your mission:** Create ConfigMap `app-config` with `MODE=production` and Secret `app-secret` with `TOKEN=cka123`. Create `config-test` Pod running `busybox:1.36` with sleep; expose both as environment variables `MODE` and `TOKEN`.

**Pass when:** Both environment variables visible in the container.

**Check yourself:**

```bash
kubectl -n cka-d02 exec config-test -- printenv MODE TOKEN
```

## Exercise 02.3 — Node affinity (12 min)

**Your mission:** Label one worker node `disk=ssd` (record its name). Create Pod `ssd-pod`, `nginx:1.27`, with **required** nodeAffinity selecting `disk=ssd`.

**Pass when:** Pod Ready on the labeled worker; required affinity exists.

**Check yourself:**

```bash
kubectl -n cka-d02 get pod ssd-pod -o wide
```

## Exercise 02.4 — Taint and toleration (12 min)

**Your mission:** On that same worker, add taint `dedicated=exam:NoSchedule`. Create `tolerant-pod` using `nginx:1.27`, required affinity to `disk=ssd`, toleration for that taint. **Remove the taint after verifying**.

**Pass when:** Pod runs on the intended worker; toleration recorded.

**Check yourself:**

```bash
kubectl -n cka-d02 describe pod tolerant-pod
```

## Exercise 02.5 — Probes & resource limits (15 min)

**Your mission:** Create Deployment `healthy-web`, 2 replicas on `nginx:1.27`, readiness and liveness HTTP probes for `/` on port 80, CPU request `100m`, memory limit `128Mi`.

**Pass when:** Both replicas Ready, correct probes and resources.

**Check yourself:**

```bash
kubectl -n cka-d02 get deploy healthy-web -o yaml
```

## End of day

Run:

```bash
bash days/day02/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
