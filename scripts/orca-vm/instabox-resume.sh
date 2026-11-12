#!/usr/bin/env bash
set -euo pipefail
export ORCA_VM_MODE="${ORCA_VM_MODE:-resume}"
exec node "$(dirname "$0")/instabox.cjs" "$@"
