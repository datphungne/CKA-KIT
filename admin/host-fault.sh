#!/usr/bin/env bash
# Explicitly guarded, deliberately destructive faults ON DEDICATED kind node containers only.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/lib/common.sh"
# Do NOT require API health: recovery MUST still work while the API server is down.
require_cmd kubectl
require_cmd kind
require_cmd docker
actual="$(kubectl config current-context 2>/dev/null || true)"
if [[ "$actual" != "$EXPECTED_CONTEXT" ]]; then
  echo "REFUSED: active Kubernetes context is '$actual', not '$EXPECTED_CONTEXT'." >&2
  exit 2
fi
if [[ $# -ne 3 || "$3" != "--confirm" ]]; then
  echo 'Usage: bash admin/host-fault.sh {kubelet|apiserver|scheduler} {stop|break|restore} --confirm' >&2
  echo 'CAUTION: breaks Kubernetes components in your disposable lab.' >&2
  exit 2
fi
component="$1"; action="$2"
case "$component:$action" in
  kubelet:stop|kubelet:restore|apiserver:break|apiserver:restore|scheduler:break|scheduler:restore) ;;
  *) echo "Unsupported fault/action: $component $action" >&2; exit 2 ;;
esac
if ! kind get clusters | grep -Fxq cka-14d; then
  echo 'REFUSED: missing dedicated cka-14d kind cluster.' >&2; exit 2
fi
case "$component" in
  kubelet)
    node=cka-14d-worker2
    if [[ "$action" == stop ]]; then
      docker exec "$node" systemctl stop kubelet
      echo "kubelet stopped on $node; restore: bash admin/host-fault.sh kubelet restore --confirm"
    else
      docker exec "$node" systemctl start kubelet
      echo "kubelet start requested on $node; run kubectl get nodes -w"
    fi ;;
  apiserver|scheduler)
    node=cka-14d-control-plane
    case "$component" in
      apiserver) fname=kube-apiserver.yaml ;;
      scheduler) fname=kube-scheduler.yaml ;;
    esac
    target="/etc/kubernetes/manifests/$fname"
    saved="/var/tmp/cka-fault-backup-$fname"
    if [[ "$action" == break ]]; then
      # Verify original is healthy and ensure no stale backup is being overwritten.
      if docker exec "$node" test -e "$saved"; then
        echo "REFUSED: $saved already exists; restore first." >&2; exit 2
      fi
      docker exec "$node" cp "$target" "$saved"
      # An invalid command flag is inserted under the existing command array.
      docker exec "$node" sh -c "sed -i '/- kube-\(apiserver\|scheduler\)$/a\\    - --cka-training-invalid-flag=true' '$target'"
      echo "Static Pod manifest modified: $fname. Diagnose using crictl on $node."
      echo "Restore: bash admin/host-fault.sh $component restore --confirm"
    else
      docker exec "$node" test -e "$saved" || { echo 'Backup missing; refusing to guess original configuration.' >&2; exit 2; }
      docker exec "$node" cp "$saved" "$target"
      docker exec "$node" rm "$saved"
      echo "Original static Pod manifest restored: $fname. Monitor kube-system Pods."
    fi ;;
esac
