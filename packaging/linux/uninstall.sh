#!/usr/bin/env bash
# Usage: sudo packaging/linux/uninstall.sh [--purge]
#   --purge  also delete the allowlist database and the group
set -euo pipefail

APP=usb-whitelist-guard
GROUP=usb-whitelist-guard
PREFIX=/opt/$APP
DATA_DIR=/var/lib/$APP
BIN_DIR=/usr/local/bin
SHARE_DIR=/usr/local/share
UNIT=$APP-monitor.service
UNIT_PATH=/etc/systemd/system/$UNIT

log() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

PURGE=false
case ${1:-} in
    "") ;;
    --purge) PURGE=true ;;
    *) die "unknown option: $1" ;;
esac

[[ $EUID -eq 0 ]] || die "run as root: sudo $0"

if [[ -f $UNIT_PATH ]]; then
    log "Removing $UNIT"
    systemctl disable --now "$UNIT" || true
    rm -f "$UNIT_PATH"
    systemctl daemon-reload
fi

log "Removing $PREFIX and commands"
rm -rf "$PREFIX"
rm -f "$BIN_DIR/$APP-gui" "$BIN_DIR/$APP-monitor"

log "Removing the desktop entry and icons"
rm -f "$SHARE_DIR/applications/$APP.desktop"
rm -f "$SHARE_DIR"/icons/hicolor/*/apps/"$APP".png
command -v gtk-update-icon-cache >/dev/null \
    && gtk-update-icon-cache -qtf "$SHARE_DIR/icons/hicolor" || true
command -v update-desktop-database >/dev/null \
    && update-desktop-database -q "$SHARE_DIR/applications" || true

if $PURGE; then
    log "Removing $DATA_DIR and group $GROUP"
    rm -rf "$DATA_DIR"
    getent group "$GROUP" >/dev/null && groupdel "$GROUP"
else
    log "Kept $DATA_DIR and group $GROUP (use --purge to remove them)"
fi

log "Done"
