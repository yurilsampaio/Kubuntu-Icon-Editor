#!/usr/bin/env bash
set -euo pipefail
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"; rm -rf "$DATA/icon-theme-studio" "$DATA/icons/hicolor/scalable/apps/icon-theme-studio.svg" "${XDG_BIN_HOME:-$HOME/.local/bin}/icon-theme-studio" "$DATA/applications/icon-theme-studio.desktop"; update-desktop-database "$DATA/applications" 2>/dev/null || true; echo "Aplicação removida; temas preservados."
