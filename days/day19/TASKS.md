# Day 19 — Troubleshooting II: Logs, Config Errors, Pending Pods, Metrics [TOPIC LAB]

**Initialize:** From the kit root, `bash days/day19/setup.sh`. **Score:** `bash days/day19/verify.sh`.

**Workspace:** All task artifacts go to `answers/`. All Kubernetes resources go to namespace `cka-d19`. Every workload below is broken on purpose; find the cause from Kubernetes itself (`describe`, `logs`, events) before fixing it.

## Exercise 19.1 — Read the previous container's logs (10 min)

**Your mission:** Deployment `crashy` is in CrashLoopBackOff. Find the error line in the logs of the **previous** container run and save it to `answers/day19-crash.txt`. Fix the Deployment by giving it the missing environment variable with value `db.local`.

**Pass when:** File contains the error line; `crashy` is 1/1 Ready.

**Check yourself:**

```bash
kubectl -n cka-d19 logs deploy/crashy --previous
```

## Exercise 19.2 — CreateContainerConfigError (8 min)

**Your mission:** Deployment `config-app` never starts. Find out why and fix it by creating what is missing, with `LEVEL=info`.

**Pass when:** `config-app` is 1/1 Ready.

**Check yourself:**

```bash
kubectl -n cka-d19 describe pod -l app=config-app | tail -5
```

## Exercise 19.3 — Pod stuck Pending on storage (8 min)

**Your mission:** Pod `needs-storage` is Pending. Fix it without changing the Pod: create the missing object (200Mi, default StorageClass).

**Pass when:** Pod Running and its claim Bound.

**Check yourself:**

```bash
kubectl -n cka-d19 describe pod needs-storage | grep -A3 Events
```

## Exercise 19.4 — Pod stuck Pending on scheduling (8 min)

**Your mission:** Deployment `wrong-node` is Pending. It may run on any worker. Fix the Deployment itself — do **not** label any node.

**Pass when:** `wrong-node` is 1/1 Ready and no node carries a `disktype` label.

**Check yourself:**

```bash
kubectl -n cka-d19 get events --field-selector reason=FailedScheduling
```

## Exercise 19.5 — Resource monitoring (8 min)

**Your mission:** Using `kubectl top`, find the Pod in `cka-d19` that uses the most CPU and write **only its name** to `answers/day19-top.txt`.

**Pass when:** The file names the heaviest CPU consumer.

**Check yourself:**

```bash
kubectl -n cka-d19 top pods --sort-by=cpu
```

## End of day

Run:

```bash
bash days/day19/verify.sh
```
