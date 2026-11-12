# Day 06 — RBAC, Drain, Helm, Kustomize

**Initialize:** From the kit root, `bash days/day06/setup.sh`. **Score:** `bash days/day06/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d06` unless the task explicitly says otherwise.

> **Admin safety:** Cluster-wide or host actions must be performed only on the dedicated `cka-14d` kind lab or separate throwaway VMs. Read `admin/VM-TRACK.md`.

## Exercise 06.1 — Cordon / drain / uncordon (15 min)

**Your mission:** Seeded `maintenance-app` has 3 replicas. Choose a kind worker with a replica, cordon it, drain it (account for DaemonSets), verify app availability, and uncordon afterward.

**Pass when:** Worker schedulable and all 3 replicas available.

**Check yourself:**

```bash
kubectl get nodes && kubectl -n cka-d06 get deploy maintenance-app
```

## Exercise 06.2 — Namespace RBAC (15 min)

**Your mission:** Create SA `auditor`, Role `pod-reader` permitting get/list/watch Pods only, RoleBinding `auditor-binding` in `cka-d06`.

**Pass when:** SA can list Pods but cannot delete Pods.

**Check yourself:**

```bash
kubectl auth can-i list pods --as=system:serviceaccount:cka-d06:auditor -n cka-d06
```

## Exercise 06.3 — Cluster RBAC (15 min)

**Your mission:** Create SA `node-auditor` in `cka-d06`, ClusterRole `cka-d06-node-reader` with get/list/watch nodes only, ClusterRoleBinding `cka-d06-node-reader` to SA.

**Pass when:** SA can list nodes but cannot patch nodes.

**Check yourself:**

```bash
kubectl auth can-i list nodes --as=system:serviceaccount:cka-d06:node-auditor
```

## Exercise 06.4 — Helm chart offline (20 min)

**Your mission:** Install local chart `charts/mini-web` using release name `cka-d06-web` in namespace `cka-d06`; then run `helm upgrade` to set replicaCount=3.

**Pass when:** Deployment `mini-web` has 3 ready replicas and Helm release is deployed.

**Check yourself:**

```bash
helm -n cka-d06 list
```

## Exercise 06.5 — Kustomize & extensions (20 min)

**Your mission:** Apply the provided Kustomize overlay `materials/kustomize/overlays/exam` after changing its image tag and replica count to `nginx:1.27`, 2 replicas. Inspect one CRD in your cluster (e.g. Calico). **VM bonus:** execute a supported kubeadm upgrade on throwaway VMs.

**Pass when:** `overlay-web` has 2 Ready replicas on correct image.

**Check yourself:**

```bash
kubectl -n cka-d06 get deploy overlay-web
```

## End of day

Run:

```bash
bash days/day06/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
