#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "============================================="
echo "   Linux Microphone Noise Suppression Setup"
echo "============================================="
echo ""

# 1. Detect Package Manager and Install Dependencies
detect_and_install() {
    echo "[1/5] Detecting Linux distribution and installing dependencies..."
    if [ -f /etc/arch-release ]; then
        echo "Detected Arch Linux."
        sudo pacman -Sy --needed --noconfirm noise-suppression-for-voice alsa-utils
    elif [ -f /etc/debian_version ]; then
        echo "Detected Debian/Ubuntu."
        sudo apt-get update
        sudo apt-get install -y noise-suppression-for-voice alsa-utils
    elif [ -f /etc/fedora-release ]; then
        echo "Detected Fedora."
        sudo dnf install -y ladspa-noise-suppression-for-voice alsa-utils
    else
        echo "⚠️  Unsupported distribution. Please manually install 'noise-suppression-for-voice' and 'alsa-utils' first."
    fi
}

# Run the installation
detect_and_install

# 2. Adjust Hardware ALSA Mixer Levels to Stop Clipping/Static Noise
echo ""
echo "[2/5] Adjusting hardware mixer settings to stop analog clipping..."

# Find the physical sound card (skip loopback and HDMI if possible)
CARD_ID=$(aplay -l 2>/dev/null | grep -i "analog" | head -n 1 | cut -d' ' -f2 | tr -d ':')
if [ -z "$CARD_ID" ]; then
    CARD_ID=$(amixer cards 2>/dev/null | grep -vi "loopback" | grep -vi "hdmi" | head -n 1 | awk '{print $1}')
fi
if [ -z "$CARD_ID" ]; then
    CARD_ID="0"
fi

echo "Using ALSA Sound Card ID: $CARD_ID"

# Reset Boost to 0dB and Capture to ~50%
amixer -c "$CARD_ID" sset 'Mic Boost' 0 2>/dev/null || amixer sset 'Mic Boost' 0 2>/dev/null || true
amixer -c "$CARD_ID" sset 'Capture' 50% 2>/dev/null || amixer sset 'Capture' 50% 2>/dev/null || true

# 3. Find the Active Physical PipeWire Source
echo ""
echo "[3/5] Auto-detecting your physical microphone in PipeWire..."

DEFAULT_SOURCE=""

# Try finding via pactl
if command -v pactl &> /dev/null; then
    DEFAULT_SOURCE=$(pactl get-default-source 2>/dev/null || true)
fi

# If default source is loopback or empty, look for physical PCI card
if [ -z "$DEFAULT_SOURCE" ] || [[ "$DEFAULT_SOURCE" == *"loopback"* ]] || [[ "$DEFAULT_SOURCE" == *"aloop"* ]]; then
    if command -v pw-link &> /dev/null; then
        DEFAULT_SOURCE=$(pw-link -l | grep "alsa_input.pci-" | head -n 1 | cut -d':' -f1 || true)
    fi
fi

# Cleanup formatting
DEFAULT_SOURCE=$(echo "$DEFAULT_SOURCE" | tr -d '[]* ')

if [ -z "$DEFAULT_SOURCE" ]; then
    echo "❌ Error: Could not automatically detect a physical microphone name."
    echo "Please find it using: 'pw-link -l | grep alsa_input'"
    exit 1
fi

echo "Target physical source: $DEFAULT_SOURCE"

# 4. Locate the plugin file dynamically on the system
echo ""
echo "[4/5] Locating noise suppression plugin..."
PLUGIN_PATH=$(find /usr/lib /usr/lib64 /usr/local/lib /var/lib -name librnnoise_ladspa.so 2>/dev/null | head -n 1 || true)

if [ -z "$PLUGIN_PATH" ]; then
    PLUGIN_PATH="/usr/lib/ladspa/librnnoise_ladspa.so"
fi
echo "Using plugin library: $PLUGIN_PATH"

# 5. Generate the PipeWire Denoising Module Config
echo "Creating PipeWire configuration..."
mkdir -p "$HOME/.config/pipewire/pipewire.conf.d"

cat << EOF > "$HOME/.config/pipewire/pipewire.conf.d/99-input-denoising.conf"
context.modules = [
    {
        name = libpipewire-module-filter-chain
        args = {
            node.description = "Noise Canceling Source"
            media.name = "Noise Canceling Source"
            filter.graph = {
                nodes = [
                    {
                        type = ladspa
                        name = rnnoise
                        plugin = $PLUGIN_PATH
                        label = noise_suppressor_mono
                        control = {
                            "VAD Threshold (%)" 50.0
                            "VAD Grace Period (ms)" 200
                        }
                    }
                ]
            }
            capture.props = {
                node.name = "capture.rnnoise_source"
                node.passive = true
                audio.rate = 48000
                target.object = "$DEFAULT_SOURCE"
            }
            playback.props = {
                node.name = "rnnoise_source"
                media.class = "Audio/Source"
                audio.rate = 48000
            }
        }
    }
]
EOF

echo "Saved configuration to $HOME/.config/pipewire/pipewire.conf.d/99-input-denoising.conf"

# 6. Restart PipeWire (as user, NOT root)
echo ""
echo "[5/5] Restarting PipeWire audio services..."
systemctl --user restart pipewire

echo ""
echo "============================================="
echo "🎉 SUCCESS: Setup is complete!"
echo "============================================="
echo "1. Open your Sound/Audio settings."
echo "2. Select 'Noise Canceling Source' as your input microphone."
echo "============================================="
