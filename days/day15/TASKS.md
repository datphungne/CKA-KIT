# Day 15 — etcd Backup & Restore, Certificates, Static Pods [TOPIC LAB]

**Initialize:** From the kit root, `bash days/day15/setup.sh`. **Score:** `bash days/day15/verify.sh`.

**Workspace:** All task artifacts go to `answers/`. All Kubernetes resources go to namespace `cka-d15` unless the task explicitly says otherwise.

**Node access:** open a node shell like `ssh` in the exam: `kubectl debug node/cka-14d-control-plane -it --profile=sysadmin --image=busybox:1.36`, then `chroot /host`. `etcdctl` and `etcdutl` are installed on the control-plane node.

> **Warning:** 15.2 restores etcd for the **whole lab cluster**. Every change made anywhere between your backup and the restore is rolled back. If the API server does not come back, recreate the cluster from the console.

## Exercise 15.1 — etcd snapshot on the control plane (15 min)

**Your mission:** On `cka-14d-control-plane`, take an etcd snapshot with `etcdctl` to `/opt/cka-etcd/backup.db`, using the endpoint and TLS files that the etcd static Pod manifest uses. Verify it with `etcdutl snapshot status`.

**Pass when:** `/opt/cka-etcd/backup.db` is a valid snapshot taken after this lab was prepared.

**Check yourself:**

```bash
etcdutl snapshot status /opt/cka-etcd/backup.db -w table
```

## Exercise 15.2 — Restore etcd from the snapshot (25 min)

**Your mission:** ConfigMap `keep-me` already exists. After your 15.1 backup, create ConfigMap `after-backup`. Then restore `/opt/cka-etcd/backup.db` with `etcdutl snapshot restore` into the **new** directory named in ConfigMap `etcd-drill` (key `restoreDir`, normally `/var/lib/etcd-from-backup`), and point the etcd static Pod at it by changing only the `hostPath` of its data volume. When etcd is back, restart `kube-apiserver`, `kube-controller-manager` and `kube-scheduler` so none of them keeps serving data cached from before the restore.

**Pass when:** etcd runs from `restoreDir`, kube-apiserver was restarted after etcd, `keep-me` exists, `after-backup` is gone, and all nodes are Ready.

**Check yourself:**

```bash
kubectl -n cka-d15 get configmap keep-me after-backup
```

## Exercise 15.3 — Certificate expiration (10 min)

**Your mission:** On the control plane, check the expiration of all kubeadm-managed certificates and save the full output to `answers/day15-certs.txt`.

**Pass when:** The file contains the kubeadm expiration table including `apiserver`.

**Check yourself:**

```bash
kubeadm certs check-expiration
```

## Exercise 15.4 — Add a user with a CertificateSigningRequest (20 min)

**Your mission:** Create a private key and CSR for user `jane` (group `cka-devs`) with `openssl`. Submit it as CertificateSigningRequest `jane` (signer `kubernetes.io/kube-apiserver-client`, usage `client auth`), approve it, and build `answers/day15-jane.kubeconfig` with the issued certificate. Grant `jane` read-only access to Pods in `cka-d15` with Role `jane-pods` and RoleBinding `jane-binding`.

**Pass when:** CSR approved and issued; `jane` can list but not delete Pods in `cka-d15`; kubeconfig saved.

**Check yourself:**

```bash
kubectl auth can-i list pods --as jane -n cka-d15
```

## Exercise 15.5 — Static Pod on a worker (12 min)

**Your mission:** Make the kubelet on `cka-14d-worker` run a static Pod `static-web` (`nginx:1.27`) in namespace `cka-d15`. Find the kubelet's `staticPodPath` first.

**Pass when:** Mirror Pod `static-web-cka-14d-worker` is Running in `cka-d15`.

**Check yourself:**

```bash
kubectl -n cka-d15 get pod static-web-cka-14d-worker -o wide
```

## End of day

Run:

```bash
bash days/day15/verify.sh
```
