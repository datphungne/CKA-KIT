#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
reset_day 20
echo "Preparing Day 20..."
require_cmd helm
helm -n "$NS" uninstall rollback-web >/dev/null 2>&1 || true
echo "Day 20 ready. Read: $ROOT/days/day20/TASKS.md"
