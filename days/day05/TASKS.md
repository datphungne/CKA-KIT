# Day 05 — kubeadm, Control Plane & etcd [ADMIN TRACK]

**Initialize:** From the kit root, `bash days/day05/setup.sh`. **Score:** `bash days/day05/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d05` unless the task explicitly says otherwise.

> **Admin safety:** Cluster-wide or host actions must be performed only on the dedicated `cka-14d` kind lab or separate throwaway VMs. Read `admin/VM-TRACK.md`.

**Node access:** the lab terminal has no Docker access. Open a shell on a node the way you would `ssh` in the exam: `kubectl debug node/cka-14d-control-plane -it --profile=sysadmin --image=busybox:1.36`, then `chroot /host`. Delete the `node-debugger-*` Pods when you are done.

## Exercise 05.1 — Inspect kubeadm init setup (15 min)

**Your mission:** On the disposable kind control-plane container, locate `/etc/kubernetes/manifests/` and `/etc/kubernetes/admin.conf`. Save results of `kubeadm version` and `kubectl get nodes` into `answers/day05-cluster.txt`.

**Pass when:** You identify 1 control plane and 2 workers.

**Check yourself:**

```bash
kubectl debug node/cka-14d-control-plane -it --profile=sysadmin --image=busybox:1.36 -- chroot /host kubeadm version
```

## Exercise 05.2 — Create a join command (12 min)

**Your mission:** Inside the kind control-plane container, use `kubeadm token create --print-join-command`. Record a **redacted** form in `answers/day05-join.txt`. Do not publish a live token.

**Pass when:** Valid join-command structure, token redacted.

**Check yourself:**

```bash
kubectl debug node/cka-14d-control-plane -it --profile=sysadmin --image=busybox:1.36 -- chroot /host kubeadm token list
```

## Exercise 05.3 — Static control-plane Pods (12 min)

**Your mission:** Inspect API server, scheduler, controller-manager, and etcd static Pod manifest paths. Save a summary of at least 2 flags for each into `answers/day05-static-pods.txt`.

**Pass when:** All four components, two actual flags each.

**Check yourself:**

```bash
kubectl debug node/cka-14d-control-plane -it --profile=sysadmin --image=busybox:1.36 -- chroot /host ls /etc/kubernetes/manifests
```

## Exercise 05.4 — etcd snapshot (20 min)

**Your mission:** On an isolated disposable cluster, run `etcdctl snapshot save` inside the etcd container using Kubernetes-managed TLS credentials and save backup to an accessible path. Verify snapshot status (or inspect with `etcdutl`). Never run restore against your shared lab cluster.

**Pass when:** Snapshot verified and saved outside the live data directory.

**Check yourself:**

```bash
kubectl -n kube-system get pod -l component=etcd
```

## Exercise 05.5 — kubeadm join / restore [VM ONLY] (40 min)

**Your mission:** Using a **separate pair of throwaway Linux VMs**, initialize a control plane using kubeadm, install a CNI and join worker; practice restoring a snapshot on a disposable clone. This cannot be honestly simulated by creating an extra Pod in kind.

**Pass when:** VM cluster Ready and restored resources verified.

**Check yourself:**

```bash
Manual host check; use admin/VM-TRACK.md
```

## End of day

Run:

```bash
bash days/day05/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.
