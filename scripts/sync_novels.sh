#!/usr/bin/env bash
set -euo pipefail

# sync_novels.sh — Merge + rsync novels DB, EPUBs, and Calibre library between devices.
#
# Usage:
#   sync_novels.sh push user@host:~     # local → remote
#   sync_novels.sh pull user@host:~     # remote → local
#   sync_novels.sh push user@host:~ --dry-run

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_DIR="$SCRIPT_DIR/python"
KNOWLEDGE_DIR="$HOME/github/knowledge"
CALIBRE_DIR="$HOME/Calibre Library"
MERGE_SCRIPT="$PYTHON_DIR/merge_novels.py"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[sync]${NC} $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC} $*"; }
error() { echo -e "${RED}[error]${NC} $*" >&2; }

usage() {
    echo "Usage: $0 <push|pull> <user@host:remote_base> [--dry-run]"
    echo ""
    echo "  push   Merge local data into remote, then rsync to remote"
    echo "  pull   Merge remote data into local, then rsync from remote"
    echo ""
    echo "Examples:"
    echo "  $0 push user@laptop:~"
    echo "  $0 pull user@desktop:~"
    echo "  $0 push user@laptop:~ --dry-run"
    exit 1
}

[[ $# -lt 2 ]] && usage

DIRECTION="$1"
REMOTE="$2"
DRY_RUN="${3:-}"

if [[ "$DIRECTION" != "push" && "$DIRECTION" != "pull" ]]; then
    error "Direction must be 'push' or 'pull'"
    usage
fi

# Verify merge script exists
if [[ ! -f "$MERGE_SCRIPT" ]]; then
    error "Merge script not found: $MERGE_SCRIPT"
    exit 1
fi

# Check for calibredb
if ! command -v calibredb &>/dev/null; then
    warn "'calibredb' not found — Calibre sync will be skipped"
fi

# Check for python3
if ! command -v python3 &>/dev/null; then
    error "python3 not found"
    exit 1
fi

RSYNC_OPTS=(-avz --progress)
[[ "$DRY_RUN" == "--dry-run" ]] && RSYNC_OPTS+=(--dry-run)

do_rsync() {
    rsync "${RSYNC_OPTS[@]}" "$@"
}

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

if [[ "$DIRECTION" == "push" ]]; then
    info "=== PUSH: local → $REMOTE ==="

    # 1. Rsync knowledge dir to remote (DBs + EPUBs)
    info "Syncing knowledge directory..."
    do_rsync "$KNOWLEDGE_DIR/" "$REMOTE/github/knowledge/"

    # 2. Rsync Calibre library to remote
    if [[ -d "$CALIBRE_DIR" ]]; then
        info "Syncing Calibre library..."
        do_rsync "$CALIBRE_DIR/" "$REMOTE/Calibre Library/"
    fi

    # 3. Merge on remote: pull remote DB, merge local into it, push back
    info "Merging databases on remote..."
    REMOTE_DB="$REMOTE/github/knowledge/novels_digest.db"
    LOCAL_DB="$KNOWLEDGE_DIR/novels_digest.db"

    # Pull remote DB to temp (if it exists)
    if scp "$REMOTE:$REMOTE_DB" "$TMPDIR/remote_novels.db" 2>/dev/null; then
        # Remote DB exists — merge local into remote
        info "Remote DB found. Merging local data into it..."
        python3 "$MERGE_SCRIPT" "$LOCAL_DB" "$TMPDIR/remote_novels.db" $DRY_RUN
        if [[ "$DRY_RUN" != "--dry-run" ]]; then
            scp "$TMPDIR/remote_novels.db" "$REMOTE:$REMOTE_DB"
            info "Merged DB pushed to remote."
        fi
    else
        info "No remote DB yet — local DB is already synced via rsync."
    fi

    info "Push complete."

elif [[ "$DIRECTION" == "pull" ]]; then
    info "=== PULL: $REMOTE → local ==="

    # 1. Pull remote DB to temp
    info "Pulling remote databases..."
    REMOTE_DB="$REMOTE/github/knowledge/novels_digest.db"
    LOCAL_DB="$KNOWLEDGE_DIR/novels_digest.db"

    if scp "$REMOTE:$REMOTE_DB" "$TMPDIR/remote_novels.db" 2>/dev/null; then
        # 2. Merge remote into local
        info "Merging remote data into local DB..."
        python3 "$MERGE_SCRIPT" "$TMPDIR/remote_novels.db" "$LOCAL_DB" $DRY_RUN
        if [[ "$DRY_RUN" != "--dry-run" ]]; then
            info "Local DB updated with merged data."
        fi
    else
        warn "No remote novels_digest.db found — skipping merge."
    fi

    # 3. Rsync EPUBs from remote (get any EPUBs the remote compiled)
    info "Syncing EPUBs from remote..."
    do_rsync --include='*.epub' --exclude='*' \
        "$REMOTE/github/knowledge/" "$KNOWLEDGE_DIR/"

    # 4. Rsync Calibre library from remote
    if ssh "$REMOTE" test -d "$HOME/Calibre Library" 2>/dev/null; then
        info "Syncing Calibre library from remote..."
        do_rsync "$REMOTE/Calibre Library/" "$CALIBRE_DIR/"
    else
        warn "No Calibre library on remote — skipping."
    fi

    info "Pull complete."
fi

info "Done. Summary:"
echo "  Local DB:  $LOCAL_DB"
echo "  Remote:    $REMOTE"
echo "  Direction: $DIRECTION"
