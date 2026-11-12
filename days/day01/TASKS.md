# Day 01 — kubectl Core Objects

**Initialize:** From the kit root, `bash days/day01/setup.sh`. **Score:** `bash days/day01/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d01` unless the task explicitly says otherwise.

## Exercise 01.1 — Create a Pod (6 min)

**Your mission:** Create `web-pod` in `cka-d01`, `nginx:1.27`, container `web`, `containerPort: 80`, label `app=web`. Use an imperative command or YAML.

**Pass when:** Pod Running/Ready and image exactly `nginx:1.27`.

**Check yourself:**

```bash
kubectl -n cka-d01 get pod web-pod -o wide
```

## Exercise 01.2 — Scale a Deployment (8 min)

**Your mission:** Create Deployment `frontend` with image `nginx:1.27` and 3 replicas. Scale up to 5 and down to 3.

**Pass when:** Desired=updated=ready=3.

**Check yourself:**

```bash
kubectl -n cka-d01 get deploy frontend
```

## Exercise 01.3 — Generate YAML without an editor (8 min)

**Your mission:** Create Pod `cache-pod` using `redis:7` by first generating a YAML file at `answers/day01-cache.yaml` with `--dry-run=client -o yaml`; then apply it.

**Pass when:** Pod Ready; file present on your local machine.

**Check yourself:**

```bash
kubectl -n cka-d01 get pod cache-pod -o yaml
```

## Exercise 01.4 — Selectors and filtering (7 min)

**Your mission:** Three example Pods already exist: `sample-front-a`, `sample-front-b`, `sample-back`. Save sorted names of `tier=frontend` Pods to `answers/day01-frontend.txt`, one name per line.

**Pass when:** File contains exactly two frontend Pod names.

**Check yourself:**

```bash
kubectl -n cka-d01 get pods -l tier=frontend
```

## Exercise 01.5 — JSONPath export (8 min)

**Your mission:** Use kubectl JSONPath to export all Pod names in namespace `cka-d01` to `answers/day01-pods.txt`, **sorted**, one name per line.

**Pass when:** File exactly matches the live Pod name set, including your new Pods.

**Check yourself:**

```bash
kubectl -n cka-d01 get pods -o jsonpath="{.items[*].metadata.name}"
```

## End of day

Run:

```bash
bash days/day01/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
