#!/bin/bash
set -euo pipefail

readonly HYPR_DIR="${HOME}/.config/hypr"
readonly THEME_SCRIPT="${HYPR_DIR}/theme/scripts/system-theme.sh"

current_theme="$("${THEME_SCRIPT}" get)"

theme_name="WhiteSur"
[[ "$current_theme" == "dark" ]] && theme_name="WhiteSurDark"

echo "Applying Qt theme: ${theme_name}"

############################
# 1. Set Kvantum theme
############################
if command -v kvantummanager &>/dev/null; then
    kvantummanager --set "${theme_name}" \
    && echo "✔ Kvantum theme set to ${theme_name}" \
    || echo "⚠ Failed to set Kvantum theme" >&2
fi

############################
# 2. Correct Qt variables (THIS FIXES DOLPHIN)
############################
export QT_STYLE_OVERRIDE=""
export QT_QPA_PLATFORMTHEME=kde

echo "✔ Qt platform theme: kde (Qt5 + Qt6)"
echo "✔ Qt style override: (using kdeglobals style: Darkly)"

############################
# 3. Persist for all sessions
############################
ENV_FILE="${HOME}/.config/environment.d/qt-theme.conf"
mkdir -p "$(dirname "$ENV_FILE")"

cat > "$ENV_FILE" <<EOF
QT_STYLE_OVERRIDE=""
QT_QPA_PLATFORMTHEME=kde
EOF

echo "✔ Environment variables persisted (${ENV_FILE})"
echo "✅ Dolphin and all Qt apps fixed"
