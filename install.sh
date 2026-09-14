#!/usr/bin/env bash
set -e

echo "========================================================"
echo "    Installing DLSS Enabler for Linux (Cross-Distro)    "
echo "========================================================"

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor"

mkdir -p "$BIN_DIR" "$APPS_DIR"

# 1. Symlink or copy launcher script
echo "-> Installing launcher executable to $BIN_DIR/dlss-enabler-gui..."
ln -sf "$INSTALL_DIR/dlss-enabler" "$BIN_DIR/dlss-enabler-gui"
chmod +x "$INSTALL_DIR/dlss-enabler"

# 2. Install desktop icon in standard sizes
echo "-> Installing application icons..."
for size in 32 48 64 128 256; do
    target_dir="$ICONS_DIR/${size}x${size}/apps"
    mkdir -p "$target_dir"
    if [ -f "$INSTALL_DIR/assets/icon_${size}x${size}.png" ]; then
        cp "$INSTALL_DIR/assets/icon_${size}x${size}.png" "$target_dir/dlss-enabler.png"
    fi
done

# SVG scalable icon
mkdir -p "$ICONS_DIR/scalable/apps"
if [ -f "$INSTALL_DIR/assets/icon.svg" ]; then
    cp "$INSTALL_DIR/assets/icon.svg" "$ICONS_DIR/scalable/apps/dlss-enabler.svg"
fi

# 3. Install .desktop file
echo "-> Installing desktop launcher..."
DESKTOP_SRC="$INSTALL_DIR/dlss-enabler.desktop"
DESKTOP_DEST="$APPS_DIR/dlss-enabler.desktop"

# Ensure Exec points directly to full path if ~/.local/bin is not in PATH
sed "s|Exec=dlss-enabler-gui|Exec=$BIN_DIR/dlss-enabler-gui|g" "$DESKTOP_SRC" > "$DESKTOP_DEST"
chmod +x "$DESKTOP_DEST"

# Update desktop database if available
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo ""
echo "✓ Installation completed successfully!"
echo "You can now launch DLSS Enabler from your application menu or run:"
echo "    dlss-enabler-gui"
echo ""
