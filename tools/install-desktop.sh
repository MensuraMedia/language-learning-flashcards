#!/usr/bin/env bash
#
# Install Japanese Practice as a desktop application for the current user.
#
# Installs into its own virtualenv under ~/.local/opt, puts a launcher on PATH,
# and registers an icon and menu entry. Nothing is written outside $HOME and no
# root is needed.
#
# The installed copy is **independent of this source tree** — the wheel is built
# and installed non-editable, so moving or deleting the checkout afterwards does
# not break the application. Re-run this script to upgrade.
#
#   ./tools/install-desktop.sh
#   ./tools/install-desktop.sh --prefix ~/somewhere/else
#
set -euo pipefail

PREFIX="${HOME}/.local/opt/japanese-practice"
BINDIR="${HOME}/.local/bin"
APPDIR="${HOME}/.local/share/applications"
ICONROOT="${HOME}/.local/share/icons/hicolor"
APPID="japanese-practice"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefix) PREFIX="$2"; shift 2 ;;
    -h|--help) sed -n '2,16p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SRC"

say() { printf '  %s\n' "$*"; }

echo "Installing Japanese Practice"
say "source : $SRC"
say "prefix : $PREFIX"

# --- 1. build a wheel ---------------------------------------------------------
# Built rather than installed with -e: an editable install would break the moment
# the checkout moves, which is not what "installed" should mean.
BUILD_TMP="$(mktemp -d)"
trap 'rm -rf "$BUILD_TMP"' EXIT

# setuptools reuses build/ across runs, so a file deleted from the source tree
# survives in the wheel until it is cleared. That shipped a removed audio cue
# once. Start every build from nothing.
rm -rf "$SRC/build" "$SRC"/src/*.egg-info

PY="${PYTHON:-python3}"
say "building wheel with $PY"
"$PY" -m pip install --quiet --upgrade build >/dev/null 2>&1 || true
# Build output goes to a log and is only surfaced on failure. Modern setuptools
# emits a PEP 639 deprecation notice about this project's `license = {file=...}`
# metadata; migrating to an SPDX expression needs setuptools>=77, which would
# break `pip install -e .` in older environments. The notice is not an error.
BUILD_LOG="$BUILD_TMP/build.log"
if ! "$PY" -m build --wheel --outdir "$BUILD_TMP" >"$BUILD_LOG" 2>&1; then
  echo "  build failed:" >&2
  cat "$BUILD_LOG" >&2
  exit 1
fi
WHEEL="$(ls "$BUILD_TMP"/*.whl)"
say "wheel  : $(basename "$WHEEL") ($(du -h "$WHEEL" | cut -f1))"

# --- 2. virtualenv ------------------------------------------------------------
# --system-site-packages is REQUIRED. Without it pywebview cannot import
# PyGObject (gi) and silently degrades to serving in a browser rather than
# opening a window — the failure is a missing window, with no error.
say "creating venv (--system-site-packages, required for PyGObject)"
rm -rf "$PREFIX"
"$PY" -m venv --system-site-packages "$PREFIX"
"$PREFIX/bin/pip" install --quiet --upgrade pip
"$PREFIX/bin/pip" install --quiet "$WHEEL"

if ! "$PREFIX/bin/python" -c "import gi" 2>/dev/null; then
  say "WARNING: PyGObject is not importable — the app will run in browser mode."
  say "         Install it with: sudo apt install python3-gi gir1.2-webkit2-4.0"
fi

# --- 3. launcher --------------------------------------------------------------
mkdir -p "$BINDIR"
ln -sf "$PREFIX/bin/japanese-practice" "$BINDIR/$APPID"
say "launcher: $BINDIR/$APPID"
case ":$PATH:" in
  *":$BINDIR:"*) ;;
  *) say "NOTE: $BINDIR is not on your PATH — add it to use the command directly" ;;
esac

# --- 4. icons -----------------------------------------------------------------
ICONSRC="$(dirname "$("$PREFIX/bin/python" -c 'import japanese_practice,os;print(japanese_practice.__file__)')")/static/icons"
for size in 32 64 128 256 512; do
  install -Dm644 "$ICONSRC/icon-${size}.png" "$ICONROOT/${size}x${size}/apps/$APPID.png"
done
say "icons   : 5 sizes into hicolor"

# --- 5. menu entry ------------------------------------------------------------
mkdir -p "$APPDIR"
cat > "$APPDIR/$APPID.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Japanese Practice
GenericName=Japanese Flash Cards
Comment=Learn Hiragana, Katakana and Kanji with flash cards and memory games
Exec=$BINDIR/$APPID
Icon=$APPID
Terminal=false
Categories=Education;Languages;
Keywords=japanese;hiragana;katakana;kanji;flashcards;jlpt;kana;language;
StartupNotify=true
StartupWMClass=$APPID
EOF

command -v desktop-file-validate >/dev/null && desktop-file-validate "$APPDIR/$APPID.desktop"
command -v update-desktop-database >/dev/null && update-desktop-database "$APPDIR" 2>/dev/null || true
command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -f -t "$ICONROOT" 2>/dev/null || true
say "menu    : $APPDIR/$APPID.desktop"

echo
echo "Installed. Launch it from your application menu, or run:"
echo "    $APPID"
echo
echo "Study data lives in ~/.local/share/japanese-practice/ and is NOT touched by"
echo "install or uninstall. Remove with ./tools/uninstall-desktop.sh"
