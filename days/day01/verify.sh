#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT/lib/common.sh"
require_lab_cluster
python3 "$ROOT/bin/grade.py" 1
