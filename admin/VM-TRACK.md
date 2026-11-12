# Node administration track (separate from namespace exercises)

Day 5/6/8/11/12/14 include CKA tasks requiring root on the Kubernetes control plane or workers. `kind` simulates kubeadm nodes as Docker containers; it is suitable for discovering manifests, studying kubelet, and safely testing recovery. **It is NOT equivalent to upgrading or building real Linux VMs using kubeadm.**

## Local kind track (contained, disposable)

1. Create the dedicated lab: `bash cluster/create-kind.sh`.
2. Check the context: `kubectl config current-context` must be `kind-cka-14d`.
3. Inspect control plane:
   ```bash
   docker exec cka-14d-control-plane ls -l /etc/kubernetes/manifests
   docker exec cka-14d-control-plane kubeadm version
   docker exec cka-14d-control-plane crictl ps -a
   docker exec cka-14d-worker2 journalctl -u kubelet -n 50 --no-pager
   ```
4. For faults, ALWAYS read `admin/host-fault.sh` and use exact guarded commands from Day 8/11 tasks.
5. Do **not** use the helper against workplace, production or shared clusters. Node faults can cause substantial downtime even in kind.

### etcd snapshot (kind control plane)

Find the etcd container and use `etcdctl` inside it. Some etcd images include `etcdctl` and `etcdutl` but your host may not.

```bash
# Control-plane etcd static Pod normally uses client cert/key and CA in /etc/kubernetes/pki/etcd.
# Inspect flags before running the snapshot.
docker exec cka-14d-control-plane grep -E 'listen-client-urls|trusted-ca-file|cert-file|key-file' /etc/kubernetes/manifests/etcd.yaml
# ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
#  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
#  --cert=/etc/kubernetes/pki/etcd/healthcheck-client.crt \
#  --key=/etc/kubernetes/pki/etcd/healthcheck-client.key \
#  snapshot save /tmp/cka-snapshot.db
```

Never restore over a working live etcd. Snapshot restores must use a separate throwaway control plane or a clone. Live snapshots, kubeconfig and join tokens are not to be committed.

## VM-only track (true kubeadm init/join/upgrade/restore)

Provision **two disposable Ubuntu 24.04 / RHEL-compatible Linux VMs** on Proxmox (or another hypervisor), each with at least 2 vCPU and 3–4GiB RAM. With a supported container runtime and Kubernetes packages installed:

- Confirm no production workloads exist on these machines.
- Initialize cluster with `kubeadm init` and set an appropriate Pod CIDR.
- Install a compatible CNI, then use `kubeadm token create --print-join-command` and `kubeadm join` on the worker.
- Practice `kubectl drain`, `kubectl uncordon`, plus backup and restore of etcd using a clone of the control plane.
- Upgrade between supported minor versions by following the exact Kubernetes version-specific instructions. Do not use a fixed upgrade recipe against an unknown kubeadm version.

References: https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/ ; https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/ ; https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/
