#!/bin/bash

set -e

echo "============================================="
echo "       ALSA Hardware Microphone Fix"
echo "============================================="

# Find the active physical analog sound card
echo "Detecting physical sound card..."
CARD_ID=$(aplay -l 2>/dev/null | grep -i "analog" | head -n 1 | cut -d' ' -f2 | tr -d ':')

if [ -z "$CARD_ID" ]; then
    CARD_ID=$(amixer cards 2>/dev/null | grep -vi "loopback" | grep -vi "hdmi" | head -n 1 | awk '{print $1}')
fi

if [ -z "$CARD_ID" ]; then
    CARD_ID="0"
fi

echo "Using ALSA Sound Card ID: $CARD_ID"

# Reset Boost to 0dB and Capture volume to 50% to prevent static/clipping
echo "Applying mixer thresholds..."
amixer -c "$CARD_ID" sset 'Mic Boost' 0 2>/dev/null || amixer sset 'Mic Boost' 0 2>/dev/null || true
amixer -c "$CARD_ID" sset 'Capture' 50% 2>/dev/null || amixer sset 'Capture' 50% 2>/dev/null || true

# Persist state (requires root via NOPASSWD sudoers entry)
echo "Saving hardware states to system profile..."
sudo alsactl store

echo "============================================="
echo "🎉 ALSA settings applied and saved successfully!"
echo "============================================="
