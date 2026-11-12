# CKA-KIT · Real Kubernetes Practice Console

**14 days · 70 hands-on CKA exercises · one local web interface · real Kubernetes cluster.**

A local-first study environment. The dashboard is a small web app running at `http://127.0.0.1:8765` on your machine, and it controls **actual Kubernetes resources** in a disposable, three-node `kind` cluster. The terminal is a real Bash PTY, not a command simulator. There is no hosted service, account, or remote cluster.

> **Important:** This app can open a shell on your computer and seed/delete resources on its dedicated practice cluster. Never expose its HTTP port to other devices or the public Internet. Use it only on your own trusted computer.

## Start with one command

**Prerequisites:** Linux, macOS or **Windows WSL2**, Docker Desktop/Engine running, `kind` v0.33+, `kubectl`, `python3` with `venv`, `git`, `bash`, and `curl`. Recommended at least 8 GB free RAM and 3+ CPU cores. Internet is needed initially to install Python dependencies, download images, and load terminal fonts/assets. Use WSL2 bash on Windows (not PowerShell).

```bash
git clone https://github.com/datphungne/CKA-KIT.git
cd CKA-KIT
./start.sh
```

Open **http://127.0.0.1:8765** in your browser. The web interface provides:

1. **Create Cluster** — creates a named disposable `kind-cka-14d` cluster (one control plane + two workers) and installs Calico CNI. Initial setup may take several minutes depending on image downloads.
2. **Choose Day 01–14** in the left navigation.
3. **Prepare Lab** — seeds the real namespaces, broken workloads and exercises. **WARNING:** preparing a day again resets its namespace and deletes your previous lab resources.
4. **Real Terminal** — run `kubectl`, `vim`, `helm`, `bash`, etc. Terminal commands execute locally as your user in a pseudo-terminal. It starts with a context-minified kubeconfig containing only `kind-cka-14d` and the selected namespace. The shell is **not a sandbox**: you can still change environment variables or access your local files, so do not run untrusted commands.
5. **Resources / Events** — live API information, no mock data.
6. **Verify all tasks** — runs the existing `days/dayXX/verify.sh` read-only grader; reports PASS / FAIL / MANUAL. Grades are saved only in your browser's local storage.

**First time:** choose **Create Cluster**, then click **Prepare Lab** for Day 1. No need to navigate daily folders manually.

### How to stop

Press `Ctrl+C` in the terminal running `./start.sh`. This stops the local website **but leaves your Kubernetes practice cluster intact**, so you can continue the next day. To remove the entire lab permanently:

```bash
bash cluster/delete-kind.sh --confirm-delete
```

## What is real vs. not included?

| Feature | Implementation |
| --- | --- |
| Pod / Deployment / Service / Node state | Real `kubectl` calls to Kubernetes API |
| Shell / kubectl / editing manifests | Real local Bash PTY over WebSocket |
| Setup / reset of daily labs | Existing shell scripts from each `days/dayXX/` folder |
| Automated checking | Existing `bin/grade.py` against live Kubernetes state |
| NetworkPolicies | Calico networking, not simulated rules |
| kubeadm joins, upgrades and etcd restoration | **Must be performed on separate disposable VMs.** A kind cluster is not an equivalent replacement |
| Ingress, Gateway API and metrics-server | Only available when their controllers are installed; see `cluster/addons.md` |
| Official CKA score | Not available. Exam-like scores are custom self-assessment only |

## Architecture

```text
Browser localhost:8765
  ├── 14-day exercise UI + progress + resource explorer
  ├── WebSocket terminal ────── Bash PTY ── kubectl / helm / vim
  └── REST API ── safe action registry ── setup.sh / verify.sh
                     │
              kind-cka-14d (Docker)
              ├── control-plane
              ├── worker
              └── worker   + Calico NetworkPolicy
```

Only loopback address `127.0.0.1` is bound. No external hosting or user account. API actions are a fixed allow-list, and the grader/setup scripts check that `kubectl`'s current context is `kind-cka-14d`. The browser terminal has an isolated default kubeconfig, but it is still a host shell and has your normal host permissions.

## Terminal assets

The UI loads xterm.js and a fit addon from jsDelivr CDN. If you are offline, a simple shell input fallback is shown; for a fully interactive TTY, load the xterm assets while connected. The local backend runs with Python FastAPI/uvicorn installed into `.venv/` at first start.

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

For all 70 individual instructions see `WORKBOOK.md` or the **Exercises** tab. Each `days/dayXX` folder is self-contained with `TASKS.md`, `setup.sh`, `verify.sh`, `cleanup.sh`. Admin exercises involving physical kubelet, kubeadm, and etcd still require `admin/VM-TRACK.md`.

## If something goes wrong

- **Create Cluster fails:** confirm Docker is running, `kind` works and at least 8 GB free RAM is available. Click Diagnose to inspect prerequisites.
- **Kubernetes terminal disconnected:** create the cluster, verify API Ready and press ↻ in the terminal toolbar.
- **Port 8765 already in use:** close another instance of the console.
- **PermissionError / no Python venv:** install Python virtualenv support (`sudo apt install python3-venv` on Debian/Ubuntu).
- **Lab verification fails:** read the check descriptions; some exercises require local `answers/` evidence and/or manual VM work.
- **Ingress/Gateway tasks fail:** first install suitable controllers; they aren't installed automatically.

Official references: [Kubernetes Documentation](https://kubernetes.io/docs/), [kind](https://kind.sigs.k8s.io/), [Calico on kind](https://docs.tigera.io/calico/latest/getting-started/kubernetes/kind), [CKA certification](https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/).
