#!/bin/bash

# ==============================================================================
#  Archzenith Installer
#  A premium, interactive installation script for Hyprland and AGS setup.
# ==============================================================================

# ANSI Color Codes for Premium Aesthetics
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Helper Functions for Output Formatting
print_banner() {
    clear
    echo -e "${CYAN}${BOLD}"
    echo "    ___               __                      _ __  __  "
    echo "   /   |  ___________/ /_  ________  ____  (_) /_/ /_ "
    echo "  / /| | / ___/ ___/ __ \/_  /_  / / __ \/ / __/ __ \ "
    echo " / ___ |/ /  / /__/ / / / / /_/ /_/ / / / / /_/ / / / "
    echo "/_/  |_/_/   \___/_/ /_/ /___/___/_/ /_/_/\__/_/ /_/  "
    echo "                                                      "
    echo -e "         ${MAGENTA}Premium Hyprland & AGS Installer${NC}"
    echo -e "======================================================\n"
}

print_header() {
    echo -e "\n${BOLD}${CYAN}>> $1${NC}"
    echo -e "${BLUE}------------------------------------------------------${NC}"
}

print_success() {
    echo -e "${GREEN}${BOLD}✔ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}${BOLD}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}${BOLD}✘ $1${NC}"
}

# 1. Ask for Sudo Password Right at the Start
print_banner
echo -e "${BOLD}${YELLOW}🔒 Sudo privileges are required to start the installation.${NC}"
echo -e "${YELLOW}Please enter your password when prompted.${NC}\n"

# Trigger sudo refresh and keep it alive in the background
if ! sudo -v; then
    print_error "Sudo authentication failed. Exiting installer."
    exit 1
fi

# Background loop to refresh sudo timestamp while script is running
keep_sudo_alive() {
    while true; do
        sudo -n true
        sleep 60
        kill -0 "$$" || exit
    done 2>/dev/null
}
keep_sudo_alive &
print_success "Sudo authorization successful. Password won't be requested again."

# 2. Backup Existing Configuration & Deploy Archzenith Configs
print_header "System Backup & Configuration Setup"
read -rp "Would you like to back up your existing ~/.config folder before starting? [y/N]: " backup_choice
backup_choice=${backup_choice:-N}

if [[ "$backup_choice" =~ ^[Yy]$ ]]; then
    if [ -d "$HOME/.config" ]; then
        BACKUP_DEST="$HOME/.config_bak_$(date +%F_%H%M%S)"
        echo -e "${YELLOW}Moving active ~/.config to $BACKUP_DEST ...${NC}"
        mv "$HOME/.config" "$BACKUP_DEST"
        if [ $? -eq 0 ]; then
            print_success "Successfully backed up and moved ~/.config to $BACKUP_DEST"
        else
            print_error "Failed to back up ~/.config. Installation aborted for safety."
            exit 1
        fi
    else
        print_warning "~/.config directory does not exist. No backup needed."
    fi
else
    echo -e "${RED}${BOLD}⚠ Nuking existing ~/.config folder as requested...${NC}"
    rm -rf "$HOME/.config"
    print_success "Nuked existing ~/.config folder."
fi

# Automatically copy the project .config to the user ~/.config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
CONFIG_SRC="$SCRIPT_DIR/.config"

if [ -d "$CONFIG_SRC" ]; then
    echo -e "${YELLOW}Deploying project configurations to ~/.config/...${NC}"
    mkdir -p "$HOME/.config"
    
    # Copy new configurations
    for dir in "$CONFIG_SRC"/*; do
        basename_dir=$(basename "$dir")
        cp -r "$dir" "$HOME/.config/"
        print_success "Deployed: ~/.config/$basename_dir"
    done
    print_success "Archzenith configurations deployed perfectly!"
else
    print_error "Configuration source folder (.config) not found in the installer directory."
    exit 1
fi


# 2. Check and Install Yay (AUR Helper)
check_aur_helper() {
    print_header "Checking for AUR Helper"
    if command -v yay &>/dev/null; then
        print_success "Found yay: $(yay --version)"
        AUR_HELPER="yay"
    else
        print_warning "yay is not installed. We will compile and install it now..."
        sudo pacman -S --needed --noconfirm base-devel git
        
        # Clone and build yay in a temporary folder
        TEMP_DIR=$(mktemp -d)
        git clone https://aur.archlinux.org/yay.git "$TEMP_DIR/yay"
        cd "$TEMP_DIR/yay" || exit
        makepkg -si --noconfirm
        cd - &>/dev/null || exit
        rm -rf "$TEMP_DIR"
        
        if command -v yay &>/dev/null; then
            print_success "Successfully installed yay!"
            AUR_HELPER="yay"
        else
            print_error "Failed to install yay. An AUR helper is required for this setup."
            exit 1
        fi
    fi
}
check_aur_helper

# Define package arrays for the 7 Sections
sec1_pkgs=("aylurs-gtk-shell-git" "gst-libav" "libastal-meta" "dart-sass" "sassc")
sec2_pkgs=("hyprland" "hyprcursor" "hyprlock" "hyprpaper")
sec3_pkgs=("fish" "starship" "btop" "fastfetch" "translate-shell" "polkit-gnome" "bat" "lsd" )
sec4_pkgs=("pipewire" "pamixer" "pavucontrol" "playerctl" "brightnessctl" "bluez" "bluez-utils" "blueman" "network-manager-applet" "networkmanager")
sec5_pkgs=("vlc" "noise-suppression-for-voice")
sec6_pkgs=("sddm" "gtk4" "kde-material-you-colors" "qt5ct" "qt6ct" "cwal" "lolcat")
sec7_pkgs=("cmake" "meson" "cpio" "pkg-config" "gcc")

# Interactive installer loop for each of the 7 sections
install_section() {
    local sec_num=$1
    local sec_name=$2
    local sec_desc=$3
    # Reference the package array indirectly
    local array_ref="sec${sec_num}_pkgs[@]"
    local pkgs=("${!array_ref}")

    print_header "Section $sec_num: $sec_name"
    echo -e "${BOLD}Description:${NC} $sec_desc"
    echo -e "${BOLD}Packages to be installed:${NC}"
    echo -e "${CYAN}${pkgs[*]}${NC}\n"

    read -rp "Install Section $sec_num? [Y/n]: " choice
    choice=${choice:-Y}

    if [[ "$choice" =~ ^[Yy]$ ]]; then
        echo -e "\n${YELLOW}Installing Section $sec_num packages...${NC}"
        $AUR_HELPER -Sy --needed --noconfirm "${pkgs[@]}"
        if [ $? -eq 0 ]; then
            print_success "Section $sec_num installed successfully!"
        else
            print_warning "Some packages in Section $sec_num failed to install. Continuing..."
        fi
    else
        echo -e "${YELLOW}Skipped Section $sec_num.${NC}"
    fi
}

# Run the 7 Sections
install_section 1 "Desktop Shell & Widgets" "Installs the AGS core widgets, Astal frameworks, and SASS compilation styling utilities."
install_section 2 "Window Manager & Compositor" "Installs the core Hyprland compositor, wallpaper manager, screen locker, cursor controls, and authentication policy agent."
install_section 3 "Shell, Terminal & System Utilities" "Installs user tools, alternative modern shell (Fish), prompt, system monitors, syntax systems, calculator, and backends."
install_section 4 "Hardware Control & Media" "Installs system pipewire audio, volume controllers, brightness triggers, network interfaces, and Bluetooth managers."
install_section 5 "Screenshots & Media Playback" "Installs VLC media player."
install_section 6 "Look & Feel (Themes & Fonts)" "Installs fonts, display manager theme, cursor packages, material color scheme, and configuration toolkits."
install_section 7 "Compilation Tools" "Installs base build layers, dependency compilers, package configuration, and assets utility modules."

# Configure Kitty as the system-wide default terminal
print_header "Kitty Terminal Configuration"
echo -e "${YELLOW}Setting kitty as the default terminal emulator...${NC}"

# Set TERMINAL env var in .zshrc
if ! grep -q "export TERMINAL=kitty" "$HOME/.zshrc" 2>/dev/null; then
    sed -i "1 a export TERMINAL=kitty" "$HOME/.zshrc" 2>/dev/null || \
    echo -e "\nexport TERMINAL=kitty" >> "$HOME/.zshrc"
    print_success "Added TERMINAL=kitty to ~/.zshrc"
fi

# Set KDE terminal application
mkdir -p "$HOME/.config"
if command -v kwriteconfig6 &>/dev/null; then
    kwriteconfig6 --file kdeglobals --group General --key TerminalApplication kitty
    kwriteconfig6 --file dolphinrc --group General --key TerminalApplication kitty
    print_success "Set kitty as KDE terminal application"
fi

# Create xdg-terminal-exec wrapper
mkdir -p "$HOME/.local/bin"
if [ ! -f "$HOME/.local/bin/xdg-terminal-exec" ]; then
    cat > "$HOME/.local/bin/xdg-terminal-exec" << 'XEOF'
#!/bin/bash
exec kitty "$@"
XEOF
    chmod +x "$HOME/.local/bin/xdg-terminal-exec"
    print_success "Created xdg-terminal-exec wrapper"
fi

print_success "Kitty configured as system-wide default terminal"

# Ask user if they want to install the Tela Icon Theme
print_header "Tela Icon Theme Installation"
echo -e "The ${BOLD}Tela Icon Theme${NC} is a colorful, modern, flat icon set designed for Linux."
read -rp "Would you like to download and install the Tela Icon Theme? [y/N]: " install_tela
install_tela=${install_tela:-N}

if [[ "$install_tela" =~ ^[Yy]$ ]]; then
    print_header "Downloading & Installing Tela Icon Theme"
    TEMP_DIR=$(mktemp -d)
    echo -e "${YELLOW}Cloning Tela Icon Theme repository...${NC}"
    git clone https://github.com/vinceliuice/tela-icon-theme.git "$TEMP_DIR/tela"
    if [ -d "$TEMP_DIR/tela" ]; then
        echo -e "${YELLOW}Running Tela Icon Theme installer...${NC}"
        # Running the installer to install all colors for the current user
        bash "$TEMP_DIR/tela/install.sh" -a
        print_success "Tela Icon Theme installed successfully!"
    else
        print_error "Failed to clone Tela Icon Theme repository. Trying to install via yay instead..."
        $AUR_HELPER -S --needed --noconfirm tela-icon-theme
    fi
    rm -rf "$TEMP_DIR"
else
    echo -e "${YELLOW}Skipped Tela Icon Theme installation.${NC}"
fi



# Deploy ALSA mic fix only on systems with a built-in/internal microphone
print_header "ALSA Mic Fix"
HAS_MIC=false
if command -v arecord &>/dev/null; then
    CAPTURE_DEVICES=$(arecord -l 2>/dev/null | grep -i "card")
    if [ -n "$CAPTURE_DEVICES" ]; then
        HAS_MIC=true
    fi
fi
if [ "$HAS_MIC" = false ] && command -v amixer &>/dev/null; then
    amixer scontrols 2>/dev/null | grep -qiE "mic|capture" && HAS_MIC=true
fi

if [ "$HAS_MIC" = true ]; then
    print_success "Detected a microphone — deploying ALSA mic fix"
    if [ -f "$SCRIPT_DIR/etc/sudoers.d/alsa-mic-fix" ]; then
        install -m 440 -o root -g root "$SCRIPT_DIR/etc/sudoers.d/alsa-mic-fix" /etc/sudoers.d/alsa-mic-fix 2>/dev/null && \
            print_success "Deployed sudoers rule for alsactl store" || \
            print_warning "Could not deploy sudoers rule (run manually: sudo install -m 440 etc/sudoers.d/alsa-mic-fix /etc/sudoers.d/)"
    else
        print_warning "sudoers rule file not found at etc/sudoers.d/alsa-mic-fix"
    fi
else
    print_warning "No built-in microphone detected — skipping ALSA mic fix"
fi

# Finalizing Installation
print_banner
echo -e "${GREEN}${BOLD}🎉 Installation Complete!${NC}"
echo -e "Please restart your session or log into Hyprland to load your new environment."
echo -e "Thank you for using Archzenith!\n"
