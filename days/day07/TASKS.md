# Day 07 — Broken Workloads — Fix All Five

**Initialize:** From the kit root, `bash days/day07/setup.sh`. **Score:** `bash days/day07/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d07` unless the task explicitly says otherwise.

## Exercise 07.1 — CrashLoopBackOff (12 min)

**Your mission:** `broken-app` exits immediately (`exit 1`). Change container command so it remains healthy and Running. Pod fields are immutable: recreate only this Pod with a corrected spec.

**Pass when:** Pod Ready, no continuous restarts.

**Check yourself:**

```bash
kubectl -n cka-d07 get pod broken-app
```

## Exercise 07.2 — ImagePullBackOff (9 min)

**Your mission:** Fix `broken-image` Deployment using an existing `nginx:1.27` image, without changing the Deployment name.

**Pass when:** Deployment Ready 1/1.

**Check yourself:**

```bash
kubectl -n cka-d07 rollout status deploy/broken-image
```

## Exercise 07.3 — Pending due to CPU (12 min)

**Your mission:** `pending-app` requests an impossible 1000 CPU cores. Reduce the Pod resource request to `100m` by replacing the Pod; keep name `pending-app`.

**Pass when:** Pod schedules, CPU request <= 100m.

**Check yourself:**

```bash
kubectl -n cka-d07 describe pod pending-app
```

## Exercise 07.4 — Wrong Service selector (10 min)

**Your mission:** `backend-svc` points at a missing label. Fix it to select actual `backend` Pods. Prove it has usable endpoints.

**Pass when:** EndpointSlice contains Ready backends.

**Check yourself:**

```bash
kubectl -n cka-d07 get endpointslice -l kubernetes.io/service-name=backend-svc
```

## Exercise 07.5 — Wrong readiness port (10 min)

**Your mission:** `broken-probe` Deployment probes port 9999 while nginx listens on 80. Correct only its probe settings.

**Pass when:** Deployment Ready 2/2.

**Check yourself:**

```bash
kubectl -n cka-d07 rollout status deploy/broken-probe
```

## End of day

Run:

```bash
bash days/day07/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
