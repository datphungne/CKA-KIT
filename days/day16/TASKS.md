# Day 16 — Scheduling, Quotas & Autoscaling [TOPIC LAB]

**Initialize:** From the kit root, `bash days/day16/setup.sh`. **Score:** `bash days/day16/verify.sh`.

**Workspace:** All task artifacts go to `answers/`. All Kubernetes resources go to namespace `cka-d16` unless the task explicitly says otherwise. Setup installs metrics-server if the cluster does not have it yet.

## Exercise 16.1 — ResourceQuota and LimitRange (15 min)

**Your mission:** Create ResourceQuota `ns-quota` with `pods=20`, `requests.cpu=2`, `requests.memory=2Gi`, `limits.cpu=4`, `limits.memory=4Gi`. Create LimitRange `ns-limits` giving containers a default request of `100m` CPU / `64Mi` memory and a default limit of `200m` / `128Mi`. Then create Pod `defaulted` (`nginx:1.27`) **without** a resources block.

**Pass when:** Quota and LimitRange match; Pod `defaulted` is Running with the defaults applied.

**Check yourself:**

```bash
kubectl -n cka-d16 describe quota ns-quota; kubectl -n cka-d16 get pod defaulted -o jsonpath='{.spec.containers[0].resources}'
```

## Exercise 16.2 — PriorityClass (10 min)

**Your mission:** Create PriorityClass `critical-batch` with value `1000000` and preemption policy `PreemptLowerPriority`. Run Pod `urgent` (`nginx:1.27`) with that class.

**Pass when:** Pod `urgent` is Running with priority 1000000.

**Check yourself:**

```bash
kubectl -n cka-d16 get pod urgent -o jsonpath='{.spec.priority}'
```

## Exercise 16.3 — PodDisruptionBudget (10 min)

**Your mission:** Deployment `web` runs 3 replicas. Protect it with PodDisruptionBudget `web-pdb` so that at least 2 Pods stay available during voluntary disruptions (drains).

**Pass when:** `web-pdb` selects the `web` Pods with `minAvailable: 2` and allows 1 disruption.

**Check yourself:**

```bash
kubectl -n cka-d16 get pdb web-pdb
```

## Exercise 16.4 — Spread replicas across nodes (12 min)

**Your mission:** Create Deployment `spread-web` (`nginx:1.27`, 2 replicas) whose Pods must never share a node, using **required** pod anti-affinity on `kubernetes.io/hostname`.

**Pass when:** Both replicas Ready on different nodes; required anti-affinity configured.

**Check yourself:**

```bash
kubectl -n cka-d16 get pods -l app=spread-web -o wide
```

## Exercise 16.5 — HorizontalPodAutoscaler (12 min)

**Your mission:** Autoscale Deployment `hpa-app` between 1 and 5 replicas targeting 50% average CPU utilization. Confirm metrics are flowing with `kubectl top`.

**Pass when:** HPA `hpa-app` targets the Deployment with min 1, max 5, CPU 50%, and reports a current CPU value.

**Check yourself:**

```bash
kubectl -n cka-d16 get hpa hpa-app; kubectl -n cka-d16 top pods
```

## End of day

Run:

```bash
bash days/day16/verify.sh
```
