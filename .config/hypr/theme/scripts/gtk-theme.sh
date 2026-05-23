#!/bin/bash

set -euo pipefail

readonly HYPR_DIR="${HOME}/.config/hypr"

# Run dynamic GTK theme overrides script to synchronize color scheme, set base theme and apply custom styles
if [[ -f "${HYPR_DIR}/theme/scripts/gtk-theme.py" ]]; then
    python3 "${HYPR_DIR}/theme/scripts/gtk-theme.py"
else
    echo "Error: ${HYPR_DIR}/theme/scripts/gtk-theme.py not found" >&2
    exit 1
fi
