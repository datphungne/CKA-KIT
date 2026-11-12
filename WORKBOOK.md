# CKA 14-Day Hands-on Workbook + Topic Labs

This workbook contains **70 original practice exercises**, 5 per day. All object names and specs are intentionally precise. Attempt each task without a solution, then run `verify.sh` for feedback. These are **practice exercises, not official CKA exam questions**.

## Usage

```bash
bash cluster/create-kind.sh         # once (Docker, kind, kubectl, curl required)
bash days/day01/setup.sh          # resets only namespace cka-d01
cat days/day01/TASKS.md          # read your tasks
bash days/day01/verify.sh         # automated checks; some need manual evidence
bash days/day01/cleanup.sh        # optional: clears ONLY the day's namespace
```

For **Day 5/6/8/11/12/14 node administration**, review `admin/VM-TRACK.md` and `admin/host-fault.sh`. Host failures require a **disposable kind cluster or separate VMs**; do not do them on a shared cluster. `setup.sh` itself does not break a host.

## Timing

Use the minutes per exercise as a soft time limit. Days 10/12/14: 2-hour, 100-point practice mocks. Keep at least 10 minutes for final verification.

---
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


---

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


---

# Day 03 — Services, DNS & NetworkPolicies

**Initialize:** From the kit root, `bash days/day03/setup.sh`. **Score:** `bash days/day03/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d03` unless the task explicitly says otherwise.

## Exercise 03.1 — ClusterIP (10 min)

**Your mission:** `api` Deployment (3 nginx replicas) exists. Create `api-svc` ClusterIP Service with port 8080 → targetPort 80 and selector `app=api`.

**Pass when:** Service has three ready endpoints; in-cluster curl returns HTTP 200.

**Check yourself:**

```bash
kubectl -n cka-d03 get endpointslice -l kubernetes.io/service-name=api-svc
```

## Exercise 03.2 — NodePort (10 min)

**Your mission:** Expose existing `frontend` Deployment with a `frontend-nodeport` Service on NodePort **30080**, service port 80 and target port 80. From host, test `curl http://127.0.0.1:30080` (requires kind worker port mapping).

**Pass when:** HTTP succeeds via mapped NodePort.

**Check yourself:**

```bash
kubectl -n cka-d03 get svc frontend-nodeport
```

## Exercise 03.3 — Cluster DNS (10 min)

**Your mission:** Create Service `database` targeting the seeded `database` Deployment, port 80. From `dns-client`, resolve `database.cka-d03.svc.cluster.local` and write output into `answers/day03-dns.txt`.

**Pass when:** FQDN resolves; file records the query result.

**Check yourself:**

```bash
kubectl -n cka-d03 exec dns-client -- nslookup database.cka-d03.svc.cluster.local
```

## Exercise 03.4 — Enforced network policy (20 min)

**Your mission:** Apply NetworkPolicy `database-ingress` selecting `app=database`. Allow TCP/80 ingress only from Pods labeled `role=frontend` in this namespace (`trusted` is allowed, `outsider` must be denied). Default deny applies to that selected backend.

**Pass when:** Curl from trusted succeeds; outsider fails/times out. Calico must be healthy.

**Check yourself:**

```bash
kubectl -n cka-d03 get networkpolicy database-ingress -o yaml
```

## Exercise 03.5 — Ingress and Gateway API [OPTIONAL] (20 min)

**Your mission:** With an installed Ingress controller, create Ingress `api-ingress` routing host `cka.local` and path `/` to `api-svc` port 8080. With Gateway API CRDs **and** controller, create `api-route` HTTPRoute targeting `api-svc`, and attach it to a compatible Gateway.

**Pass when:** Verify actual HTTP routing through the controllers, not just object creation.

**Check yourself:**

```bash
kubectl -n cka-d03 get ingress,httproute 2>/dev/null || true
```

## End of day

Run:

```bash
bash days/day03/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.


---

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

**Your mission:** Find an existing working StorageClass (kind often provides `standard`). Create PVC `dynamic-claim` for 1Gi with that class, then mount it to a Pod named `dynamic-reader`. If no provisioner exists, mark this task as blocked and install one in your lab.

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

**Your mission:** Confirm `cka-d04-local-pv` uses `Retain`. Delete `data-writer` and `data-claim`, observe the PV turn `Released`, and write your observations (include the word `Released`) to `answers/day04-reclaim.txt`. Then make the PV `Available` again by clearing its `claimRef`, recreate `data-claim` and `data-writer`, and confirm `/data/proof.txt` survived.

**Pass when:** PV is `Retain`, the observations file mentions `Released`, and the recreated claim/Pod still read `hello-cka` from the retained volume.

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


---

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


---

# Day 06 — RBAC, Drain, Helm, Kustomize

**Initialize:** From the kit root, `bash days/day06/setup.sh`. **Score:** `bash days/day06/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d06` unless the task explicitly says otherwise.

> **Admin safety:** Cluster-wide or host actions must be performed only on the dedicated `cka-14d` kind lab or separate throwaway VMs. Read `admin/VM-TRACK.md`.

## Exercise 06.1 — Cordon / drain / uncordon (15 min)

**Your mission:** Seeded `maintenance-app` has 3 replicas. Choose a kind worker with a replica, cordon it, drain it (account for DaemonSets), verify app availability, and uncordon afterward.

**Pass when:** Worker schedulable, all 3 replicas available, and at least one replica was evicted and rescheduled by your drain.

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


---

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


---

# Day 08 — Cluster Troubleshooting — Safe & Isolated

**Initialize:** From the kit root, `bash days/day08/setup.sh`. **Score:** `bash days/day08/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d08` unless the task explicitly says otherwise.

> **Admin safety:** Cluster-wide or host actions must be performed only on the dedicated `cka-14d` kind lab or separate throwaway VMs. Read `admin/VM-TRACK.md`.

## Exercise 08.1 — Service port failure (12 min)

**Your mission:** `upstream-svc` targets port 8081 but `upstream` nginx listens on 80. Find the cause via endpoints and Pod specs; repair.

**Pass when:** Internal HTTP request works on Service port 80.

**Check yourself:**

```bash
kubectl -n cka-d08 get svc upstream-svc -o yaml
```

## Exercise 08.2 — CoreDNS path (12 min)

**Your mission:** From `net-client`, resolve `dns-backend-svc.cka-d08.svc.cluster.local`, then inspect CoreDNS service, Deployment and logs. Save the observed DNS result to `answers/day08-dns.txt`.

**Pass when:** DNS resolves and CoreDNS Pods healthy.

**Check yourself:**

```bash
kubectl -n cka-d08 exec net-client -- nslookup dns-backend-svc
```

## Exercise 08.3 — Pod scheduling (12 min)

**Your mission:** Cordon one worker, add required affinity to a new Pod `pinned-app` for that worker and observe Pending. Then safely restore scheduling so the Pod can run; uncordon worker.

**Pass when:** pinned-app Ready, worker uncordoned.

**Check yourself:**

```bash
kubectl -n cka-d08 get pod pinned-app -o wide
```

## Exercise 08.4 — kubelet outage [ISOLATED ONLY] (25 min)

**Your mission:** On dedicated kind node `cka-14d-worker2`, stop kubelet via `admin/host-fault.sh kubelet stop --confirm`. Diagnose NotReady and restore via `admin/host-fault.sh kubelet restore --confirm`. This changes the **node container**, not your real host.

**Pass when:** All nodes Ready after restore.

**Check yourself:**

```bash
kubectl get nodes
```

## Exercise 08.5 — API server outage [ISOLATED ONLY] (30 min)

**Your mission:** Run `admin/host-fault.sh apiserver break --confirm` to insert an invalid API-server flag into its static Pod manifest on the dedicated kind control-plane node. Diagnose by `docker exec`/crictl, then `admin/host-fault.sh apiserver restore --confirm`.

**Pass when:** API server reachable; all nodes recover.

**Check yourself:**

```bash
kubectl get --raw /readyz
```

## End of day

Run:

```bash
bash days/day08/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.


---

# Day 09 — Mixed Speed Challenge

**Initialize:** From the kit root, `bash days/day09/setup.sh`. **Score:** `bash days/day09/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d09` unless the task explicitly says otherwise.

## Exercise 09.1 — Deployment rollout (8 min)

**Your mission:** Create `payments` Deployment, 4 replicas, `nginx:1.27`, RollingUpdate with maxUnavailable=1 and maxSurge=1.

**Pass when:** 4/4 Ready and specified strategy.

**Check yourself:**

```bash
kubectl -n cka-d09 get deploy payments -o yaml
```

## Exercise 09.2 — RBAC under time (10 min)

**Your mission:** Create ServiceAccount `viewer`, Role `config-reader` to get/list ConfigMaps and RoleBinding `viewer-config` in `cka-d09`.

**Pass when:** SA can list ConfigMaps but not Secrets.

**Check yourself:**

```bash
kubectl auth can-i list configmaps --as=system:serviceaccount:cka-d09:viewer -n cka-d09
```

## Exercise 09.3 — NetworkPolicy under time (12 min)

**Your mission:** Apply policy `db-allow-api` to Pods `app=db` in `cka-d09`: allow ingress TCP/80 only from Pods labeled `role=api`.

**Pass when:** Role-client allowed; random-client blocked.

**Check yourself:**

```bash
kubectl -n cka-d09 get netpol db-allow-api -o yaml
```

## Exercise 09.4 — Dynamic PVC (12 min)

**Your mission:** Create `payments-data` PVC for 2Gi using a working StorageClass. Mount to Pod `payments-writer` at `/var/lib/data`.

**Pass when:** PVC Bound and Pod Ready with mount.

**Check yourself:**

```bash
kubectl -n cka-d09 get pvc payments-data
```

## Exercise 09.5 — Broken Service (10 min)

**Your mission:** `bad-svc` was deliberately created with selector `app=missing`. Repair to expose seeded `api` Deployment.

**Pass when:** Service has ready endpoints.

**Check yourself:**

```bash
kubectl -n cka-d09 get endpointslice -l kubernetes.io/service-name=bad-svc
```

## End of day

Run:

```bash
bash days/day09/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.


---

# Day 10 — Timed Mock Exam A — 100 Points

**Initialize:** From the kit root, `bash days/day10/setup.sh`. **Score:** `bash days/day10/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d10` unless the task explicitly says otherwise.

> **Mock rule:** Complete all five sections within **120 minutes**. Each section carries the points shown in its title. Automated verification is partial and is **not** the official CKA scoring system.

## Exercise 10.1 — Cluster admin [25 pts] (25 min)

**Your mission:** Without harming your cluster, record etcd static Pod location, kubelet version, and a **validated etcd snapshot** on a disposable control plane. Save notes `answers/day10-admin.txt`.

**Pass when:** Snapshot exists; report accurately documents node/control-plane state.

**Check yourself:**

```bash
Manual inspect: admin/VM-TRACK.md
```

## Exercise 10.2 — Networking [20 pts] (25 min)

**Your mission:** Fix `backend-svc` selector. Create Service `bad-image-svc` for `bad-image` Deployment after repairing its image. Configure NetworkPolicy `trusted-only` selecting `app=backend`, permitting only Pods `role=trusted` on TCP/80.

**Pass when:** Endpoints Ready and traffic allowed/denied as specified.

**Check yourself:**

```bash
kubectl -n cka-d10 get svc,netpol
```

## Exercise 10.3 — Workloads [15 pts] (20 min)

**Your mission:** Create `mock-web` Deployment, 3 replicas, `nginx:1.27`, readiness HTTP `/:80`, ConfigMap `mock-config` setting `MODE=test`, exposed as env var `MODE`.

**Pass when:** 3/3 Ready, probe and env correctly configured.

**Check yourself:**

```bash
kubectl -n cka-d10 get deploy mock-web -o yaml
```

## Exercise 10.4 — RBAC / maintenance [25 pts] (25 min)

**Your mission:** Create SA `mock-viewer`, Role `mock-reader` get/list/watch Pods, binding `mock-reader-binding`; safely cordon/drain/uncordon a worker and record in `answers/day10-maintenance.txt`.

**Pass when:** RBAC limited to read Pods; all nodes schedulable.

**Check yourself:**

```bash
kubectl auth can-i list pods --as=system:serviceaccount:cka-d10:mock-viewer -n cka-d10
```

## Exercise 10.5 — Storage [15 pts] (25 min)

**Your mission:** Create PVC `mock-data` 1Gi via dynamic provisioner; Pod `mock-writer` using `busybox:1.36` mounts claim at `/data`. Write `mock-10` to `/data/proof.txt`.

**Pass when:** PVC Bound, Pod Ready, data readable.

**Check yourself:**

```bash
kubectl -n cka-d10 exec mock-writer -- cat /data/proof.txt
```

## End of day

Run:

```bash
bash days/day10/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.


---

# Day 11 — Advanced Troubleshooting

**Initialize:** From the kit root, `bash days/day11/setup.sh`. **Score:** `bash days/day11/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d11` unless the task explicitly says otherwise.

> **Admin safety:** Cluster-wide or host actions must be performed only on the dedicated `cka-14d` kind lab or separate throwaway VMs. Read `admin/VM-TRACK.md`.

## Exercise 11.1 — OOMKilled (15 min)

**Your mission:** `memory-hog` consumes 256Mi with 32Mi memory limit. Repair without removing memory limit entirely: set limit to **512Mi** and recreate Pod.

**Pass when:** Pod Running and not OOMKilled.

**Check yourself:**

```bash
kubectl -n cka-d11 describe pod memory-hog
```

## Exercise 11.2 — Readiness failure (12 min)

**Your mission:** Fix `probe-failure` HTTP readiness port 8088 to match nginx.

**Pass when:** Deployment 2/2 Ready.

**Check yourself:**

```bash
kubectl -n cka-d11 rollout status deploy/probe-failure
```

## Exercise 11.3 — Service targetPort (12 min)

**Your mission:** `web-svc` targets incorrect port 8082. Fix to port 80; use `diagnostics-client` for HTTP verification.

**Pass when:** Service returns HTTP 200.

**Check yourself:**

```bash
kubectl -n cka-d11 get svc web-svc
```

## Exercise 11.4 — Faulty kubeconfig [LOCAL] (15 min)

**Your mission:** Export current **lab** kubeconfig to `answers/day11-kubeconfig.yaml`. In a **copy only**, change server address to wrong endpoint; diagnose and fix the copy. Do not overwrite `~/.kube/config`.

**Pass when:** Corrected copy connects using `KUBECONFIG=... kubectl cluster-info`.

**Check yourself:**

```bash
Manual command on copied kubeconfig
```

## Exercise 11.5 — Scheduler interruption [ISOLATED ONLY] (30 min)

**Your mission:** Break `kube-scheduler` static Pod using `admin/host-fault.sh scheduler break --confirm` on kind CP. Inspect logs with Docker/crictl. Restore and verify scheduler recovery.

**Pass when:** `kube-system/kube-scheduler` Running after restore; new Pods can schedule.

**Check yourself:**

```bash
kubectl -n kube-system get pods -l component=kube-scheduler
```

## End of day

Run:

```bash
bash days/day11/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.


---

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


---

# Day 13 — Final Speed Drills

**Initialize:** From the kit root, `bash days/day13/setup.sh`. **Score:** `bash days/day13/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d13` unless the task explicitly says otherwise.

## Exercise 13.1 — kubectl sprint (10 min)

**Your mission:** Create `alpha`, `beta` Pods with nginx:1.27. Create Deployments `rapid-a` (2 replicas) and `rapid-b` (3 replicas), nginx:1.27.

**Pass when:** All ready; correct replica counts.

**Check yourself:**

```bash
kubectl -n cka-d13 get pods,deploy
```

## Exercise 13.2 — Networking sprint (12 min)

**Your mission:** Repair `gateway-svc` selector to `app=gateway`. Create NetworkPolicy `gateway-allow` allowing traffic to gateway Pods on 80 from Pods `role=tester` only (create/label client as needed).

**Pass when:** Service endpoints Ready; policy selects correct backend.

**Check yourself:**

```bash
kubectl -n cka-d13 get svc,netpol
```

## Exercise 13.3 — Storage sprint (12 min)

**Your mission:** Create 500Mi PVC `speed-data` using a working StorageClass. Mount to `speed-writer` Pod at `/data`.

**Pass when:** Claim Bound, Pod Ready.

**Check yourself:**

```bash
kubectl -n cka-d13 get pvc speed-data
```

## Exercise 13.4 — RBAC sprint (12 min)

**Your mission:** Create SA `speed-auditor`, Role `speed-reader` read-only ConfigMap access, and binding `speed-binding`.

**Pass when:** SA allowed list ConfigMaps and denied delete.

**Check yourself:**

```bash
kubectl auth can-i list configmaps --as=system:serviceaccount:cka-d13:speed-auditor -n cka-d13
```

## Exercise 13.5 — Emergency repair (12 min)

**Your mission:** Fix seeded `broken-rollout` Deployment bad image, then verify nginx is Ready.

**Pass when:** Rollout succeeds.

**Check yourself:**

```bash
kubectl -n cka-d13 rollout status deploy/broken-rollout
```

## End of day

Run:

```bash
bash days/day13/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.


---

# Day 14 — Final Mock Exam — 100 Points

**Initialize:** From the kit root, `bash days/day14/setup.sh`. **Score:** `bash days/day14/verify.sh`.

**Workspace:** All task artifacts go to `answers/` (already included). All Kubernetes resources go to namespace `cka-d14` unless the task explicitly says otherwise.

> **Admin safety:** Cluster-wide or host actions must be performed only on the dedicated `cka-14d` kind lab or separate throwaway VMs. Read `admin/VM-TRACK.md`.

> **Mock rule:** Complete all five sections within **120 minutes**. Each section carries the points shown in its title. Automated verification is partial and is **not** the official CKA scoring system.

## Exercise 14.1 — Cluster [25 pts] (25 min)

**Your mission:** Take an etcd snapshot on isolated kind CP, record control-plane static Pod path and kubelet service status in `answers/day14-admin.txt`. **Do not restore over live etcd.**

**Pass when:** Validated snapshot and correct observed cluster state.

**Check yourself:**

```bash
Manual snapshot evidence + node Ready
```

## Exercise 14.2 — Troubleshooting [30 pts] (30 min)

**Your mission:** Fix seeded `billing` Deployment bad image and `orders-svc` bad selector; additionally inspect kubelet logs inside worker2 and summarize in `answers/day14-troubleshooting.txt`.

**Pass when:** Both Deployments healthy and Service endpoints Ready.

**Check yourself:**

```bash
kubectl -n cka-d14 get deploy,svc
```

## Exercise 14.3 — Networking [20 pts] (25 min)

**Your mission:** Create ClusterIP `billing-svc` port 8080→80 to billing. Apply NetworkPolicy `orders-allow` selecting `app=orders`, allow TCP/80 only from Pods labeled `role=trusted`.

**Pass when:** Service usable; trusted client allowed, untrusted blocked.

**Check yourself:**

```bash
kubectl -n cka-d14 get svc,netpol
```

## Exercise 14.4 — Workloads [15 pts] (20 min)

**Your mission:** Create Deployment `final-web`, 3 replicas, nginx:1.27, rollingUpdate maxUnavailable=1; Secret `final-secret` TOKEN=pass; mount it as environment variable TOKEN; readiness probe `/` port 80.

**Pass when:** 3/3 Ready with correct rollout, env and readiness.

**Check yourself:**

```bash
kubectl -n cka-d14 get deploy final-web -o yaml
```

## Exercise 14.5 — Storage [10 pts] (20 min)

**Your mission:** Create `final-claim` PVC 1Gi dynamic StorageClass, Pod `final-writer` mounts `/data`; write `cka-final` in `/data/proof.txt` and verify it.

**Pass when:** PVC Bound; proof readable from running container.

**Check yourself:**

```bash
kubectl -n cka-d14 exec final-writer -- cat /data/proof.txt
```

## End of day

Run:

```bash
bash days/day14/verify.sh
```

Write down any failed steps and repeat them from a clean `setup.sh`.


---

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

---

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

---

# Day 17 — Pod Design, Security Context & StatefulSets [TOPIC LAB]

**Initialize:** From the kit root, `bash days/day17/setup.sh`. **Score:** `bash days/day17/verify.sh`.

**Workspace:** All task artifacts go to `answers/`. All Kubernetes resources go to namespace `cka-d17` unless the task explicitly says otherwise.

## Exercise 17.1 — Init container (12 min)

**Your mission:** Create Pod `init-web`: an init container `prepare` (`busybox:1.36`) writes the text `ready from init` to `index.html` in an `emptyDir` volume, and the main container `nginx` (`nginx:1.27`) serves that volume from `/usr/share/nginx/html`.

**Pass when:** Pod Running and nginx serves exactly `ready from init`.

**Check yourself:**

```bash
kubectl -n cka-d17 exec init-web -- cat /usr/share/nginx/html/index.html
```

## Exercise 17.2 — Native sidecar and container logs (12 min)

**Your mission:** Create Pod `log-pair`. Container `app` (`busybox:1.36`) appends `tick <n>` to `/var/log/app/app.log` every 2 seconds. A **native sidecar** `log-tail` (an init container with `restartPolicy: Always`) streams that file to its stdout. Both share an `emptyDir`.

**Pass when:** Pod Running and `kubectl logs log-pair -c log-tail` shows ticks.

**Check yourself:**

```bash
kubectl -n cka-d17 logs log-pair -c log-tail --tail=3
```

## Exercise 17.3 — Security context (12 min)

**Your mission:** Create Pod `secure-pod` (`busybox:1.36`, `sleep 86400`) that runs as user `1000`, group `3000`, `fsGroup` `2000`, with `runAsNonRoot`, no privilege escalation, a read-only root filesystem and **all** Linux capabilities dropped.

**Pass when:** Pod Running as UID 1000 with every listed setting present.

**Check yourself:**

```bash
kubectl -n cka-d17 exec secure-pod -- id
```

## Exercise 17.4 — Pod Security Admission (10 min)

**Your mission:** Label namespace `cka-d17` so Pod Security Admission **enforces** `baseline` and **warns** on `restricted`. Prove it: try to create a privileged Pod `priv-test` and save the rejection message to `answers/day17-psa.txt`.

**Pass when:** Namespace labels set, `priv-test` does not exist, and the file shows the PodSecurity violation.

**Check yourself:**

```bash
kubectl get ns cka-d17 --show-labels
```

## Exercise 17.5 — StatefulSet with headless Service (15 min)

**Your mission:** Create headless Service `db-headless` (port 80, selector `app=db`) and StatefulSet `db` (`nginx:1.27`, 2 replicas, `serviceName: db-headless`) with a `volumeClaimTemplates` entry `data` (100Mi, mounted at `/usr/share/nginx/html`). Resolve `db-0.db-headless.cka-d17.svc.cluster.local` from a Pod and save the output to `answers/day17-dns.txt`.

**Pass when:** 2/2 replicas Ready, claims `data-db-0` and `data-db-1` Bound, Service is headless, per-Pod DNS name recorded.

**Check yourself:**

```bash
kubectl -n cka-d17 get sts,pvc,svc
```

## End of day

Run:

```bash
bash days/day17/verify.sh
```

---

# Day 18 — Advanced Networking: Default Deny, Egress, Namespaces, Endpoints [TOPIC LAB]

**Initialize:** From the kit root, `bash days/day18/setup.sh`. **Score:** `bash days/day18/verify.sh`.

**Workspace:** All Kubernetes resources go to namespace `cka-d18` unless the task explicitly says otherwise. Setup also creates namespace `cka-d18-frontend` (label `team=frontend`) with Pod `fe-client`. In `cka-d18` you have Deployments/Services `web` and `api`, plus Pods `client` (`role=client`) and `other-client`. Do the exercises in order.

## Exercise 18.1 — Default deny with DNS allowed (15 min)

**Your mission:** Create NetworkPolicy `default-deny` that denies **all ingress and egress** for every Pod in `cka-d18`. Then create `allow-dns` so every Pod may still send DNS queries (UDP and TCP 53) to the CoreDNS Pods in `kube-system`.

**Pass when:** `client` can no longer reach `web`, but name resolution still works.

**Check yourself:**

```bash
kubectl -n cka-d18 exec client -- nslookup web; kubectl -n cka-d18 exec client -- wget -T 3 -qO- web
```

## Exercise 18.2 — Egress and ingress for one flow (15 min)

**Your mission:** Allow exactly one flow: Pods `role=client` → Pods `app=api` on TCP/80. You need an egress rule on the client side (`client-egress`) **and** an ingress rule on the server side (`api-ingress`).

**Pass when:** `client` reaches `api`; `client` still cannot reach `web`; `other-client` cannot reach `api`.

**Check yourself:**

```bash
kubectl -n cka-d18 exec client -- wget -T 3 -qO- api
```

## Exercise 18.3 — Traffic from another namespace (12 min)

**Your mission:** Create NetworkPolicy `web-from-frontend` that lets Pods from any namespace labeled `team=frontend` reach `app=web` on TCP/80.

**Pass when:** `fe-client` in `cka-d18-frontend` reaches `web.cka-d18`; `client` in `cka-d18` still cannot.

**Check yourself:**

```bash
kubectl -n cka-d18-frontend exec fe-client -- wget -T 3 -qO- web.cka-d18
```

## Exercise 18.4 — ExternalName Service (8 min)

**Your mission:** Create Service `legacy-db` of type `ExternalName` that aliases `api.cka-d18.svc.cluster.local`.

**Pass when:** `legacy-db` resolves (as a CNAME) from `client`.

**Check yourself:**

```bash
kubectl -n cka-d18 exec client -- nslookup legacy-db
```

## Exercise 18.5 — Service without selector + manual EndpointSlice (15 min)

**Your mission:** Create Service `manual-svc` (port 80, **no selector**) and an EndpointSlice `manual-svc-1` that points it at the current IP of the `api` Pod on port 80.

**Pass when:** `manual-svc` has a ready endpoint and `client` gets an HTTP response through it.

**Check yourself:**

```bash
kubectl -n cka-d18 get endpointslice -l kubernetes.io/service-name=manual-svc
```

## End of day

Run:

```bash
bash days/day18/verify.sh
```

---

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

---

# Day 20 — Extensibility: CRDs, Helm Lifecycle, Kustomize, Cluster Interfaces [TOPIC LAB]

**Initialize:** From the kit root, `bash days/day20/setup.sh`. **Score:** `bash days/day20/verify.sh`.

**Workspace:** All task artifacts go to `answers/`. All Kubernetes resources go to namespace `cka-d20` unless the task explicitly says otherwise.

## Exercise 20.1 — CustomResourceDefinition (15 min)

**Your mission:** Create CRD `backups.cka.io`: group `cka.io`, version `v1` (served and storage), **Namespaced**, kind `Backup`, plural `backups`, short name `bk`. Its OpenAPI schema requires `spec.schedule` (string) and allows `spec.retention` (integer, minimum 1).

**Pass when:** The CRD is Established with that scope, kind and schema.

**Check yourself:**

```bash
kubectl get crd backups.cka.io; kubectl explain backup.spec
```

## Exercise 20.2 — Custom resources and schema validation (8 min)

**Your mission:** Create Backup `nightly` with schedule `0 2 * * *` and retention `7`. Then try to create Backup `broken` with retention `0` and save the API server's rejection to `answers/day20-invalid.txt`.

**Pass when:** `nightly` exists with the right spec; `broken` was rejected by the schema.

**Check yourself:**

```bash
kubectl -n cka-d20 get bk
```

## Exercise 20.3 — Helm upgrade and rollback (15 min)

**Your mission:** Install `charts/mini-web` as release `rollback-web`. Upgrade it with image tag `does-not-exist` and watch the rollout fail. Roll the release back to revision 1.

**Pass when:** History shows install, failed-image upgrade and a rollback to 1; Deployment `mini-web` is Ready on `nginx:1.27`.

**Check yourself:**

```bash
helm -n cka-d20 history rollback-web
```

## Exercise 20.4 — Write your own Kustomize overlay (15 min)

**Your mission:** Under `answers/day20-kustomize/`, build a base from `materials/kustomize/base` and an overlay `overlays/prod` that sets namespace `cka-d20`, name prefix `prod-`, label `env=prod` on everything, and generates ConfigMap `web-config` with `MODE=prod`. Apply the overlay.

**Pass when:** Deployment `prod-overlay-web` Ready with label `env=prod`; a generated `prod-web-config-<hash>` ConfigMap holds `MODE=prod`.

**Check yourself:**

```bash
kubectl kustomize answers/day20-kustomize/overlays/prod
```

## Exercise 20.5 — Identify CRI, CNI and storage plumbing (8 min)

**Your mission:** Find the container runtime (with version) the nodes use, the CNI plugin that provides Pod networking, and the provisioner behind the default StorageClass. Write all three into `answers/day20-interfaces.txt`.

**Pass when:** The file names the runtime, the CNI and the provisioner correctly.

**Check yourself:**

```bash
kubectl get nodes -o wide; kubectl get storageclass
```

## End of day

Run:

```bash
bash days/day20/verify.sh
```

---

