#!/usr/bin/env bash
# Usage: sudo packaging/linux/install.sh
set -euo pipefail

APP=usb-whitelist-guard
GROUP=usb-whitelist-guard
PREFIX=/opt/$APP
DATA_DIR=/var/lib/$APP
BIN_DIR=/usr/local/bin
SHARE_DIR=/usr/local/share
UNIT=$APP-monitor.service
UNIT_PATH=/etc/systemd/system/$UNIT
PYTHON_VERSION=3.15

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)

log() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "run as root: sudo $0"
command -v systemctl >/dev/null || die "systemd is required"

find_uv() {
    if command -v uv >/dev/null; then
        command -v uv
        return
    fi
    if [[ -n ${SUDO_USER:-} ]]; then
        local home
        home=$(getent passwd "$SUDO_USER" | cut -d: -f6)
        for candidate in "$home/.local/bin/uv" "$home/.cargo/bin/uv"; do
            if [[ -x $candidate ]]; then
                echo "$candidate"
                return
            fi
        done
    fi
    die "uv not found; install it from https://docs.astral.sh/uv/"
}
UV=$(find_uv)

BUILD=$(mktemp -d)
trap 'rm -rf "$BUILD"' EXIT
export UV_CACHE_DIR=$BUILD/cache

log "Building packages"
"$UV" build --project "$REPO" --all-packages --wheel --out-dir "$BUILD/dist" --quiet
"$UV" export --project "$REPO" --frozen --all-packages --no-dev --no-emit-workspace \
    --no-hashes --output-file "$BUILD/requirements.txt" --quiet

if systemctl is-active --quiet "$UNIT"; then
    log "Stopping the running monitor"
    systemctl stop "$UNIT"
fi

log "Installing into $PREFIX"
rm -rf "$PREFIX/venv"
UV_PYTHON_INSTALL_DIR=$PREFIX/python "$UV" venv --python "$PYTHON_VERSION" \
    --managed-python "$PREFIX/venv" --quiet
"$UV" pip install --python "$PREFIX/venv/bin/python" --quiet \
    -r "$BUILD/requirements.txt" "$BUILD"/dist/*.whl
"$PREFIX/venv/bin/python" -c "import tkinter" \
    || die "the bundled Python has no Tkinter support"
chmod -R a+rX "$PREFIX"

for command in gui monitor; do
    ln -sf "$PREFIX/venv/bin/$APP-$command" "$BIN_DIR/$APP-$command"
done

log "Preparing group $GROUP and $DATA_DIR"
getent group "$GROUP" >/dev/null || groupadd --system "$GROUP"
install -d -m 2770 -o root -g "$GROUP" "$DATA_DIR"
(
    umask 007
    "$PREFIX/venv/bin/python" -c '
from usb_whitelist_guard_core.config import database_url, default_database_path
from usb_whitelist_guard_core.storage import make_engine, upgrade_schema
upgrade_schema(make_engine(database_url(default_database_path())))
'
)
chgrp -R "$GROUP" "$DATA_DIR"
find "$DATA_DIR" -type f -exec chmod 660 {} +

if [[ -n ${SUDO_USER:-} && $SUDO_USER != root ]]; then
    usermod -aG "$GROUP" "$SUDO_USER"
    ADDED_USER=$SUDO_USER
fi

log "Installing the desktop entry and icons"
for size in 16 24 32 48 64 128 256; do
    install -Dm644 "$REPO/apps/gui/src/usb_whitelist_guard_gui/icons/icon-$size.png" \
        "$SHARE_DIR/icons/hicolor/${size}x${size}/apps/$APP.png"
done
install -Dm644 "$HERE/$APP.desktop" "$SHARE_DIR/applications/$APP.desktop"
command -v gtk-update-icon-cache >/dev/null \
    && gtk-update-icon-cache -qtf "$SHARE_DIR/icons/hicolor" || true
command -v update-desktop-database >/dev/null \
    && update-desktop-database -q "$SHARE_DIR/applications" || true

log "Enabling $UNIT"
install -Dm644 "$HERE/$UNIT" "$UNIT_PATH"
systemctl daemon-reload
systemctl enable --now "$UNIT"

log "Done"
systemctl --no-pager --lines=0 status "$UNIT" || true
if [[ -n ${ADDED_USER:-} ]]; then
    echo
    echo "$ADDED_USER was added to the '$GROUP' group."
    echo "Log out and back in, then start 'USB Whitelist Guard' from the menu (no sudo)."
fi
