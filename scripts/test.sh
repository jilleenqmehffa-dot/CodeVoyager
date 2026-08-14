#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/codevoyager-uv-cache}"

(cd "$project_root/backend" && uv run pytest)
(cd "$project_root/frontend" && npm run lint && npm run build)
