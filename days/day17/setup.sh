#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 17
echo "Preparing Day 17..."
kubectl -n "$NS" run dns-client --image=busybox:1.36 --command -- sh -c 'sleep 86400'
echo "Day 17 ready. Read: $ROOT/days/day17/TASKS.md"
