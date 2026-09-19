#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; DEST="${XDG_DATA_HOME:-$HOME/.local/share}/icon-theme-studio"; BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"; DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
mkdir -p "$DEST" "$BIN" "$DATA/applications" "$DATA/icons/hicolor/scalable/apps"; rm -rf "$DEST/icon_theme_studio"; cp -a "$ROOT/icon_theme_studio" "$DEST/icon_theme_studio"
PYTHON="$ROOT/.venv/bin/python3"
if [ ! -x "$PYTHON" ]; then echo "Ambiente .venv não encontrado. Crie-o e instale PySide6 antes de instalar." >&2; exit 1; fi
"$PYTHON" -c 'import PySide6' 2>/dev/null || { echo "PySide6 não encontrado no .venv." >&2; exit 1; }
rm -rf "$DEST/venv"; cp -a "$ROOT/.venv" "$DEST/venv"
"$DEST/venv/bin/python3" -m icon_theme_studio.icon_assets --output "$DATA/icons/hicolor/scalable/apps/icon-theme-studio.png"
printf '%s\n' '#!/usr/bin/env bash' "export PYTHONPATH='$DEST'; exec '$DEST/venv/bin/python3' -m icon_theme_studio \"\$@\"" > "$BIN/icon-theme-studio"; chmod +x "$BIN/icon-theme-studio"
printf '%s\n' '[Desktop Entry]' 'Type=Application' 'Name=Icon Theme Studio' 'Comment=Crie temas de ícones personalizados' "Exec=$BIN/icon-theme-studio" "Icon=$DATA/icons/hicolor/scalable/apps/icon-theme-studio.png" 'Categories=Settings;Utility;' 'Terminal=false' > "$DATA/applications/icon-theme-studio.desktop"
rm -f "$HOME/.cache/ksycoca6_"* "$HOME/.cache/icon-cache.kcache" 2>/dev/null || true; update-desktop-database "$DATA/applications" 2>/dev/null || true; kbuildsycoca6 --noincremental >/dev/null 2>&1 || kbuildsycoca5 --noincremental >/dev/null 2>&1 || true; echo "Instalado."
