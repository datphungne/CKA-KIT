# CKA-KIT · Real Kubernetes Practice Console

**14 days · 70 hands-on CKA exercises · one local web console · a real Kubernetes cluster.**

Everything runs on your own machine. The console at `http://127.0.0.1:8765` drives **actual Kubernetes resources** in a disposable three-node [kind](https://kind.sigs.k8s.io/) cluster (Kubernetes v1.37, Calico CNI). The terminal is a real interactive Bash shell running `kubectl`, `helm` and `vim` — no simulated output, no cloud account, no hosting.

## Start with one command

**Prerequisites**

| Requirement | Notes |
| --- | --- |
| Docker Desktop (Windows/macOS) or Docker Engine + Compose v2 (Linux) | Must be running. Nothing else to install: kind, kubectl, helm and Python live inside the console image. |
| `git` | To clone the repository. |
| 8 GB free RAM, 3+ CPU cores, ~6 GB disk | The cluster is three Docker containers. |
| Internet on first run | Builds the image, pulls `kindest/node` and Calico. Later runs work from the local cache. |

```bash
git clone https://github.com/datphungne/CKA-KIT.git
cd CKA-KIT
docker compose up --build        # or ./start.sh on Linux/macOS/WSL
```

Open **http://127.0.0.1:8765**, pick a day and press **Create cluster & start** (first time only, ~3–5 minutes), then **Start Lab**.

## Daily workflow

1. **Choose Day 01–14** in the sidebar. Each day has five exercises in its own namespace `cka-dXX`.
2. **Start Lab** seeds that namespace with the day's broken workloads. Starting a day again resets only that namespace.
3. **Solve in the terminal.** The shell opens with the day's namespace as default, `k=kubectl`, tab completion, `vim`, `helm` and `$do` (`--dry-run=client -o yaml`). Save evidence files under `/workspace/answers` (persisted in a Docker volume).
4. **Resources / Events** tabs show live API data for the namespace. If the API is unreachable they say *Disconnected* instead of showing an empty list.
5. **Verify all tasks** runs `days/dayXX/verify.sh` against live cluster state and marks each task PASS / FAIL / MANUAL. Results are kept in your browser only.
6. **Clean up this day** deletes the namespace, uncordons the workers and removes the Day 02 scheduling taint/label.

### Stop, resume, remove

| Goal | Command |
| --- | --- |
| Stop the console, keep the cluster for tomorrow | `Ctrl+C` or `docker compose down` |
| Resume | `docker compose up` — the console reconnects to the existing cluster |
| Delete the practice cluster | `docker compose exec console bash cluster/delete-kind.sh --confirm-delete` |
| Also delete saved answers and lab credentials | `docker compose down -v` |

## How it is isolated

```text
Browser ── 127.0.0.1:8765 ──► console container (FastAPI)
                                 │  fixed action allow-list: create-cluster / setup / verify / cleanup / doctor
                                 │  Docker socket ──► kind: cka-14d (control-plane + 2 workers, Calico)
                                 │
                                 └─ WebSocket ──► per-session terminal container
                                                   no Docker socket · no host files · all capabilities dropped
                                                   512 MiB / 128 PIDs · lab-only kubeconfig (read-only volume)
```

- **Your own kubeconfig is never mounted.** Lab credentials come from `kind get kubeconfig --name cka-14d`.
- **Every script verifies cluster identity before acting.** `lib/safety.py` checks that the target is the kind control-plane container labelled `cka-14d` and that its CA matches the kubeconfig in use. A context merely *named* `kind-cka-14d` that points elsewhere is refused, so setup/cleanup/grading can never hit a non-lab cluster.
- **Loopback only.** The port is bound to `127.0.0.1`; mutating requests and terminal WebSockets must come from the same origin.
- **Lab workloads cannot reach the console.** The console joins kind's network to talk to the API server, so it refuses every connection whose TCP source is a kind subnet (terminals and Pods), regardless of forged `Host`/`Origin` headers (`lib/netguard.py`).
- **Learner files are never executed.** The Day 11 kubeconfig check only accepts inline credentials — `exec`, `auth-provider` and file-path fields are rejected before `kubectl` sees the file.
- **Caveat:** the *console* container holds the Docker socket so it can manage kind. That is root-equivalent on the Docker host — do not expose port 8765 or run the console on a shared machine.

## What is real vs. not included

| Feature | Implementation |
| --- | --- |
| Pods / Deployments / Services / Nodes | Real `kubectl` against the Kubernetes API |
| Terminal | Real Bash PTY in an isolated container, streamed with xterm.js (bundled locally) |
| Lab setup / reset / cleanup | The `setup.sh` / `cleanup.sh` scripts in each `days/dayXX/` |
| Grading | `bin/grade.py` against live cluster state |
| NetworkPolicy | Enforced by Calico, not simulated |
| kubeadm join/upgrade, etcd restore, kubelet repair | **Need separate disposable VMs** — see `admin/VM-TRACK.md`. Shown as MANUAL by the grader. |
| Ingress, Gateway API, metrics-server | Not installed by default — see `cluster/addons.md` |
| Official CKA score | Not available. Mock-exam scores are self-assessment only. |

## Daily content

| Day | Focus | Day | Focus |
| --- | --- | --- | --- |
| 01 | Core objects | 08 | Cluster recovery |
| 02 | Workloads / scheduling | 09 | Speed challenge |
| 03 | Networking / services | 10 | Mock exam I |
| 04 | Persistent storage | 11 | Advanced recovery |
| 05 | Cluster architecture, etcd | 12 | Mock exam II |
| 06 | Maintenance, RBAC, Helm | 13 | Final speed drills |
| 07 | App troubleshooting | 14 | Final mock |

All 70 instructions are in `WORKBOOK.md` and in the **Exercises** tab. Each `days/dayXX/` folder contains `TASKS.md`, `setup.sh`, `verify.sh` and `cleanup.sh`.

## Pinned versions

kind v0.33.0 · `kindest/node:v1.37.0` (digest pinned in `cluster/create-kind.sh`) · kubectl v1.37.0 · Helm v3.22.1 · Calico v3.33.0. Calico v3.33 requires Kubernetes ≥ 1.36; keep `KUBECTL_VERSION` in the `Dockerfile` in step with the node image.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest                                  # unit + contract tests, no cluster needed

# Full lifecycle on a real cluster (setup → verify → cleanup for all 14 days, ~11 min):
docker compose up -d --build                      # then create the cluster once in the UI
CKA_INTEGRATION=1 python -m pytest tests/test_integration.py -v
```

The unit suite covers the cluster-identity guard, the HTTP/WebSocket contract (origin checks, action allow-list, single-action lock), terminal container isolation flags, shell-script syntax, namespace validation and grader coverage. The integration suite also asserts that a freshly seeded day never auto-passes a task, that a container on the kind network gets 403 from the console, and that a kubeconfig with an `exec` plugin is rejected without running it.

## Troubleshooting

- **Create cluster fails:** open **Diagnose**. Make sure Docker is running with ≥ 8 GB RAM. A failed creation removes the half-built cluster automatically, so you can retry.
- **Cluster shows *Degraded*:** the API is up but some nodes are NotReady. Right after creation this is Calico still starting; otherwise check `kubectl get nodes` / `kubectl describe node`, or recreate the cluster.
- **Terminal disconnected:** press ↻ in the terminal toolbar. Up to four terminals can be open at once.
- **Port 8765 already in use:** another console is running — `docker compose down` in that checkout.
- **A task stays FAIL:** read its *Pass when* line. Some tasks need evidence files in `/workspace/answers`; admin tasks are MANUAL by design.

References: [Kubernetes docs](https://kubernetes.io/docs/) · [kind](https://kind.sigs.k8s.io/) · [Calico on kind](https://docs.tigera.io/calico/latest/getting-started/kubernetes/kind) · [CKA certification](https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/)
