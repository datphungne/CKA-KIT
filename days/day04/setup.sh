#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 04
echo "Preparing Day 04..."

require_cmd docker
# A local PV requires a prepared directory ON THE CORRECT kind worker.
docker exec cka-14d-worker sh -c 'rm -rf /var/local/cka-d04 && mkdir -p /var/local/cka-d04'
kubectl delete pv cka-d04-local-pv --ignore-not-found --wait=true --timeout=120s >/dev/null || true
kubectl delete storageclass cka-d04-manual --ignore-not-found >/dev/null || true
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: v1
kind: Pod
metadata:
  name: storage-client
spec:
  containers:
  - name: main
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]
MANIFEST
echo "Day 04 ready. Read: $ROOT/days/day04/TASKS.md"
echo 'Inspect state: kubectl -n '"$NS"' get all'
