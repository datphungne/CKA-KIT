# CKA-KIT — 14 Days of Kubernetes Practice

**70 hands-on labs · 14 days · copy/paste setup · automated grading · no lectures.**

A self-contained practice kit for [Certified Kubernetes Administrator (CKA)](https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/). These are original exercises, not official exam questions. Built for a **disposable** Kubernetes v1.37 cluster (kind v0.33.0) and Calico v3.33.0. Some administrator exercises require additional throwaway VMs.

## Requirements

- Linux, macOS, or Windows **WSL2** terminal with Docker Desktop/Engine working
- `kind` v0.33.0 or newer, `kubectl`, `docker`, `curl`, `python3`, `bash`
- `helm` for Day 6, 6–8 GB available RAM and at least 3 available CPUs (more recommended)
- Internet connection to pull cluster/node/application images and Calico manifests

## Quick start

```bash
# Download the kit
git clone https://github.com/datphungne/CKA-KIT.git
cd CKA-KIT

# Run ONCE. This creates 1 control plane + 2 workers, installs Calico.
bash cluster/create-kind.sh
bash cluster/doctor.sh

# Every day: seed -> do tasks yourself -> verify -> optionally clean
bash days/day01/setup.sh
cat days/day01/TASKS.md
# ... now do all five exercises in the cluster ...
bash days/day01/verify.sh
bash days/day01/cleanup.sh

# Continue on Day 2:
bash days/day02/setup.sh
cat days/day02/TASKS.md
```

Replace `day01` with `day02` ... `day14`. All commands assume the **repository root**, not the `days/` directory.

## Practice workflow

1. `bash days/dayXX/setup.sh`: resets only `cka-dXX`, seeds prerequisite/broken objects; read its output.
2. `cat days/dayXX/TASKS.md`: tasks, timebox, success criteria, suggested manual inspection commands.
3. Solve independently with `kubectl`. Put required local evidence/YAML in `answers/` (gitignored).
4. `bash days/dayXX/verify.sh`: read-only checks; outputs PASS/FAIL/MANUAL.
5. Repeat failed tasks. Re-run setup to reset that day's namespace and start fresh.

**DANGER:** Setup is destructive **inside the day's namespace**. Do not run it after completing a day unless you want to reset work. Scripts explicitly refuse any kubectl context except `kind-cka-14d`. Cluster-wide exercises still affect the dedicated kind cluster.

## Daily curriculum

| Day | Topic | Practice |
|---|---|---|
| 01 | Core objects | Pods, Deployments, generated YAML, selectors, JSONPath |
| 02 | Workloads | Rollouts, ConfigMaps, Secrets, affinity, tolerations, probes |
| 03 | Networking | ClusterIP, NodePort, DNS, NetworkPolicy; optional Ingress/Gateway |
| 04 | Storage | Local PV, PVC, dynamic provisioning, retention |
| 05 | kubeadm & etcd | Static Pods, join commands, snapshots, VM-only bootstrap/restore |
| 06 | Admin/RBAC | Drain, Roles, Helm chart, Kustomize overlays |
| 07 | App recovery | CrashLoop, image pull, Pending CPU, Service, probes |
| 08 | Cluster recovery | DNS, scheduling, kubelet and API server controlled failures |
| 09 | Speed drills | Five timed mixed tasks |
| 10 | Mock #1 | Five integrated tasks, 120 minutes, 100 practice points |
| 11 | Advanced recovery | OOM, probes, Services, kubeconfig, scheduler fault |
| 12 | Mock #2 | Admin, workload, networking, storage, 120 minutes |
| 13 | Final sprint | Rapid exercises across domains |
| 14 | Final mock | Five integrated tasks, 120 minutes |

Full 70-exercise text is in [WORKBOOK.md](WORKBOOK.md) and individually in `days/dayXX/TASKS.md`.

## Extras

- `cluster/create-kind.sh` + `cluster/kind-config.yaml`: sets up multi-node lab; installs Calico via Tigera Operator so NetworkPolicies are enforced.
- `cluster/doctor.sh`: checks prerequisites, nodes and installed capabilities.
- `cluster/addons.md`: how optional Ingress/Gateway/metrics-server controller requirements differ.
- `admin/VM-TRACK.md`: instructions for kubeadm, etcd and VM-only exercises.
- `admin/host-fault.sh`: explicitly guarded fault injector for **kind node containers only**. Requires `--confirm`. **Restore actions do not depend on the API server**, so recovery works during outages.
- `charts/mini-web`: small local Helm chart, Day 6.
- `materials/kustomize/`: base + editable overlay, Day 6.
- `bin/grade.py`: state-based self-checks. Manual-admin exercises are never falsely marked as automatically passed.
- `answers/`: local scratch files, intentionally ignored by Git.

## Safety and limitations

- **Do not run on production/shared clusters**. The labs intentionally create invalid Pods, network policies, resource requests and (only on explicit confirmation) control-plane faults.
- `kind` runs Kubernetes nodes as containers. For truly representative `kubeadm init`, worker join, minor-version upgrade, etcd restore, use separate disposable VMs per `admin/VM-TRACK.md`.
- Ingress/Gateway controllers and metrics-server are **not** included. Optional exercises require those addons. An Ingress object alone does not provide working routing.
- Day 10/12/14 point totals are custom practice scores; the checker only awards points for verifiable criteria, labels admin evidence MANUAL, and never asserts official scoring.
- Runtime integration requires a working Docker/Kubernetes host; static validity of scripts alone cannot guarantee your local networking/cloud constraints.

## Delete everything

```bash
bash cluster/delete-kind.sh --confirm-delete
```

This permanently deletes the **named disposable kind cluster** and all lab resources. It does not delete any other Kubernetes cluster or Docker containers.

## References

- [Official Kubernetes docs](https://kubernetes.io/docs/)
- [kind releases](https://github.com/kubernetes-sigs/kind/releases)
- [Calico install on kind](https://docs.tigera.io/calico/latest/getting-started/kubernetes/kind)
