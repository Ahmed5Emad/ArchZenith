#!/bin/bash

TMP=/tmp
AGS_TMP="$TMP/ags-${USER}"
SRC=$HOME/.config/hypr/scripts-c
CONFIG_DIR=$HOME/.config
USER=$(whoami)

mkdir -p "$TMP"
mkdir -p "$AGS_TMP"

gcc "$SRC/battery-check.c"   -o "$TMP/battery-check"
gcc "$SRC/wallpaper-loop.c"  -o "$TMP/wallpaper-loop"

ags bundle "$CONFIG_DIR/ags/app.tsx" "$AGS_TMP/ags-bin"

# Run in background after kill any existing loop and AGS
pkill -f "wallpaper-loop" 2>/dev/null
pkill -f "ags-bin" 2>/dev/null
pkill -f "dmFyIF-ags.js" 2>/dev/null

nohup "$TMP/wallpaper-loop" >/dev/null 2>&1 &
nohup "$AGS_TMP/ags-bin" >/dev/null 2>&1 &

# Run immediately once
nohup /tmp/battery-check >/dev/null 2>&1 &

# Check if cronie is running (if the service is installed)
if systemctl list-unit-files cronie.service &>/dev/null; then
    if ! systemctl is-active --quiet cronie; then
        action=$(notify-send \
            --app-name="Hypr Scripts" \
            --expire-time=0 \
            --action=enable:"Enable Cronie" \
            "Cronie not running" \
            "Cron jobs will not execute")
        
        # FIRST action = index 0
        case "$action" in
            0)
                echo "Enabling Cronie..."
                pkexec systemctl enable --now cronie && systemctl start cronie
            ;;
        esac
    fi
fi

# Update crontab with session variables only if crontab is available
if command -v crontab &>/dev/null; then
    {
        crontab -l 2>/dev/null | grep -v "$TMP"
        # Added XDG_RUNTIME_DIR so notify-send can reach your desktop
        echo "*/5 * * * * XDG_RUNTIME_DIR=/run/user/$(id -u) $TMP/battery-check" # Check battery every 5 minutes
    } | crontab - || notify-send "Error" "Failed to update crontab"
fi
