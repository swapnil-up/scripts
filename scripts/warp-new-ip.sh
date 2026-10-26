#!/bin/bash
# warp-new-ip.sh — rotate the Cloudflare WARP registration to get a new IP

set -euo pipefail

if ! command -v warp-cli >/dev/null 2>&1; then
	echo "warp-cli not found; run the bootstrap to install cloudflare-warp" >&2
	exit 1
fi

warp-cli disconnect || true
warp-cli registration delete || true
warp-cli --accept-tos registration new
warp-cli connect
warp-cli status
