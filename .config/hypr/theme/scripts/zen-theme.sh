#!/bin/bash
set -euo pipefail

readonly COLORS_JSON="${HOME}/.cache/cwal/colors.json"
readonly ZEN_CONFIG_DIR="${HOME}/.config/zen"
readonly PROFILES_INI="${ZEN_CONFIG_DIR}/profiles.ini"

if [[ ! -f "$COLORS_JSON" ]]; then
    echo "No cwal colors.json found; skipping Zen theme sync"
    exit 0
fi

find_default_profile() {
    awk -F= '
        /^\[Install/ { in_install=1 }
        in_install && /^Default=/ { print $2; exit }
    ' "$PROFILES_INI"
}

profile_path="${ZEN_CONFIG_DIR}/$(find_default_profile 2>/dev/null)"
if [[ -z "$profile_path" || ! -d "$profile_path" ]]; then
    echo "Zen profile not found; skipping"
    exit 0
fi

chrome_dir="${profile_path}/chrome"
mkdir -p "$chrome_dir"

jq '{background: .special.background, foreground: .special.foreground, accent: (.colors.color4 // .colors.color3 // "#499646")}' "$COLORS_JSON" > "${chrome_dir}/current-theme.json"
