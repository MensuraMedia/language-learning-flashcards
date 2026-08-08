#!/usr/bin/env bash
#
# Remove the desktop installation made by install-desktop.sh.
#
# **Your study history is never touched.** ~/.local/share/japanese-practice/
# holds the databases, profiles and audio cache, and is left alone — uninstalling
# an application should not delete the years of practice done with it. Pass
# --purge only if you genuinely want that data gone.
#
#   ./tools/uninstall-desktop.sh
#   ./tools/uninstall-desktop.sh --purge
#
set -euo pipefail

PREFIX="${HOME}/.local/opt/japanese-practice"
BINDIR="${HOME}/.local/bin"
APPDIR="${HOME}/.local/share/applications"
ICONROOT="${HOME}/.local/share/icons/hicolor"
DATADIR="${XDG_DATA_HOME:-$HOME/.local/share}/japanese-practice"
APPID="japanese-practice"
PURGE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --purge) PURGE=1; shift ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

say() { printf '  %s\n' "$*"; }

echo "Removing Japanese Practice"
rm -rf "$PREFIX";                    say "venv    : $PREFIX"
rm -f  "$BINDIR/$APPID";             say "launcher: removed"
rm -f  "$APPDIR/$APPID.desktop";     say "menu    : removed"
for size in 32 64 128 256 512; do
  rm -f "$ICONROOT/${size}x${size}/apps/$APPID.png"
done;                                say "icons   : removed"

command -v update-desktop-database >/dev/null && update-desktop-database "$APPDIR" 2>/dev/null || true
command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -f -t "$ICONROOT" 2>/dev/null || true

if [[ $PURGE -eq 1 ]]; then
  echo
  echo "  --purge given. This deletes ALL study history, every profile and the"
  echo "  audio cache in $DATADIR"
  read -r -p "  Type DELETE to confirm: " reply
  if [[ "$reply" == "DELETE" ]]; then
    rm -rf "$DATADIR"
    say "data    : deleted"
  else
    say "data    : kept (not confirmed)"
  fi
else
  echo
  say "Study data kept at $DATADIR"
  say "Re-installing will pick it up again. Use --purge to remove it."
fi
