#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/codevoyager-uv-cache}"

cleanup() {
  trap - INT TERM EXIT
  kill 0 2>/dev/null || true
}
trap cleanup INT TERM EXIT

(cd "$project_root/backend" && uv run backend) &
(cd "$project_root/frontend" && npm run dev:desktop) &

wait
