#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 15
echo "Preparing Day 15..."
ensure_node_etcdctl
# Pick a restore target that is not the live data directory (earlier attempts may have switched to it).
live="$(node_exec cka-14d-control-plane sh -c "grep -E '^ +path: /var/lib/etcd' /etc/kubernetes/manifests/etcd.yaml | awk '{print \$2}'")"
target=/var/lib/etcd-from-backup
n=2
while [[ "$target" == "$live" ]]; do target="/var/lib/etcd-from-backup-$n"; n=$((n + 1)); done
node_exec cka-14d-control-plane rm -rf "$target" /opt/cka-etcd
kubectl -n "$NS" create configmap etcd-drill --from-literal=restoreDir="$target" --from-literal=dataDirAtSetup="$live"
kubectl -n "$NS" create configmap keep-me --from-literal=purpose="must survive the restore"
echo "etcd data dir now: $live; restore into: $target"
echo "Day 15 ready. Read: $ROOT/days/day15/TASKS.md"
