#!/usr/bin/env bash
set -e

echo "Uninstalling DLSS Enabler for Linux..."

rm -f "$HOME/.local/bin/dlss-enabler-gui"
rm -f "$HOME/.local/share/applications/dlss-enabler.desktop"
rm -f "$HOME/.local/share/icons/hicolor/*/apps/dlss-enabler.png"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/dlss-enabler.svg"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi

echo "✓ Uninstalled successfully."
