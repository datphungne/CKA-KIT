#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 05
echo "Preparing Day 05..."
kubectl -n "$NS" apply -f - <<'MANIFEST'
apiVersion: v1
kind: Pod
metadata:
  name: cluster-observer
spec:
  containers:
  - name: main
    image: busybox:1.36
    command: ["sh", "-c", "sleep 86400"]
MANIFEST
echo "Day 05 ready. Read: $ROOT/days/day05/TASKS.md"
echo 'Inspect state: kubectl -n '"$NS"' get all'
