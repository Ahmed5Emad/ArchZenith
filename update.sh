#!/bin/bash

# ==============================================================================
#  Archzenith Configuration Update Utility
#  A safe, premium utility for users to update their active ~/.config from repo.
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

# Base Directories
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
ACTIVE_DIR="$HOME/.config"
REPO_CONFIG_DIR="$REPO_DIR/.config"

# Core Archzenith Target Configs
TARGETS=("ags" "cava" "fastfetch" "fish" "hypr" "kitty" "pipewire" "starship.toml")

# Help/Usage menu
show_usage() {
    echo -e "${CYAN}${BOLD}"
    echo "    ___               __                      _ __  __  "
    echo "   /   |  ___________/ /_  ________  ____  (_) /_/ /_ "
    echo "  / /| | / ___/ ___/ __ \/_  /_  / / __ \/ / __/ __ \ "
    echo " / ___ |/ /  / /__/ / / / / /_/ /_/ / / / / /_/ / / / "
    echo "/_/  |_/_/   \___/_/ /_/ /___/___/_/ /_/_/\__/_/ /_/  "
    echo -e "         ${MAGENTA}System Update Utility${NC}"
    echo -e "======================================================\n"
    echo -e "${BOLD}Usage:${NC} ./update.sh [flags]"
    echo -e "\n${BOLD}Flags:${NC}"
    echo -e "  ${YELLOW}-d, --dry-run${NC}   Perform a simulation of the update (does not copy/delete)"
    echo -e "  ${YELLOW}-y, --yes${NC}       Skip confirmation prompt"
    echo -e "  ${YELLOW}-h, --help${NC}      Show this help menu"
    exit 0
}

# Parse flags
DRY_RUN=false
SKIP_PROMPT=false

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -y|--yes)
            SKIP_PROMPT=true
            shift
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            echo -e "${RED}${BOLD}Error: Unknown parameter '$1'${NC}"
            show_usage
            ;;
    esac
done

# Ensure diff is installed
if ! command -v diff &>/dev/null; then
    echo -e "${RED}${BOLD}Error: 'diff' utility is required but not installed.${NC}"
    exit 1
fi

# Banner styling
echo -e "${CYAN}${BOLD}======================================================${NC}"
echo -e "  ${BOLD}${MAGENTA}Archzenith Updater: ${CYAN}STARTING${NC}"
echo -e "  Pulling latest changes from GitHub & preparing update..."
echo -e "${CYAN}${BOLD}======================================================${NC}\n"

# 1. Fetch latest changes from remote Git repository
if [ -d "$REPO_DIR/.git" ]; then
    echo -e "${BOLD}${CYAN}>> Pulling latest commits from GitHub...${NC}"
    if git -C "$REPO_DIR" pull; then
        echo -e "${GREEN}${BOLD}✔ Successfully fetched latest commits!${NC}\n"
    else
        echo -e "${YELLOW}${BOLD}⚠ Warning: Git pull failed or offline. Proceeding with current local repository files...${NC}\n"
    fi
else
    echo -e "${YELLOW}${BOLD}⚠ Warning: No git repository detected. Skipping git pull...${NC}\n"
fi

# 2. Compile planned updates (exclusively pull changes: Repo -> Active)
DIFFERENCES_FOUND=false

OPS_TYPE=()
OPS_SRC=()
OPS_DST=()
OPS_DESC=()
OPS_REL=()

for item in "${TARGETS[@]}"; do
    REPO_PATH="$REPO_CONFIG_DIR/$item"
    ACTIVE_PATH="$ACTIVE_DIR/$item"
    
    if [[ -e "$REPO_PATH" ]] || [[ -e "$ACTIVE_PATH" ]]; then
        # Handle cases where the target only exists in one place at the root level
        if [[ ! -e "$REPO_PATH" ]]; then
            # Repository deleted the entire target config folder, so we delete it locally
            DIFFERENCES_FOUND=true
            OPS_TYPE+=("delete")
            OPS_SRC+=("")
            OPS_DST+=("$ACTIVE_PATH")
            OPS_DESC+=("Deleted ")
            OPS_REL+=(".config/$item")
            continue
        elif [[ ! -e "$ACTIVE_PATH" ]]; then
            # Repository created a new target config folder, so we copy it locally
            DIFFERENCES_FOUND=true
            OPS_TYPE+=("copy")
            OPS_SRC+=("$REPO_PATH")
            OPS_DST+=("$ACTIVE_PATH")
            OPS_DESC+=("Created ")
            OPS_REL+=(".config/$item")
            continue
        fi

        # Both exist, run brief diff scan with complete cache and log exclusions
        DIFF_OUT=$(diff -rq \
            --exclude='cache' \
            --exclude='logs' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='*.pyo' \
            --exclude='.git' \
            --exclude='current.conf' \
            "$REPO_PATH" "$ACTIVE_PATH" 2>/dev/null)
        
        if [[ -n "$DIFF_OUT" ]]; then
            DIFFERENCES_FOUND=true
            
            while IFS= read -r line; do
                if [[ -z "$line" ]]; then
                    continue
                fi
                
                if [[ "$line" =~ ^Files\ (.*)\ and\ (.*)\ differ$ ]]; then
                    REPO_FILE="${BASH_REMATCH[1]}"
                    ACTIVE_FILE="${BASH_REMATCH[2]}"
                    REL_PATH=${ACTIVE_FILE#"$HOME/"}
                    
                    OPS_TYPE+=("copy")
                    OPS_SRC+=("$REPO_FILE")
                    OPS_DST+=("$ACTIVE_FILE")
                    OPS_DESC+=("Modified")
                    OPS_REL+=("$REL_PATH")
                    
                elif [[ "$line" =~ ^Only\ in\ (.*):\ (.*)$ ]]; then
                    DIR="${BASH_REMATCH[1]}"
                    FILE="${BASH_REMATCH[2]}"
                    FULL_PATH="$DIR/$FILE"
                    
                    if [[ "$DIR" == "$ACTIVE_DIR"* ]]; then
                        # Created locally, but doesn't exist in repo. We delete it to match the repo!
                        REL_PATH=${FULL_PATH#"$HOME/"}
                        OPS_TYPE+=("delete")
                        OPS_SRC+=("")
                        OPS_DST+=("$FULL_PATH")
                        OPS_DESC+=("Deleted ")
                        OPS_REL+=("$REL_PATH")
                    else
                        # Created in repo. We copy it locally!
                        REPO_REL_PATH=${FULL_PATH#"$REPO_DIR/"}
                        OPS_TYPE+=("copy")
                        OPS_SRC+=("$FULL_PATH")
                        OPS_DST+=("$HOME/$REPO_REL_PATH")
                        OPS_DESC+=("Created ")
                        OPS_REL+=("$REPO_REL_PATH")
                    fi
                fi
            done <<< "$DIFF_OUT"
        fi
    fi
done

if [ "$DIFFERENCES_FOUND" = false ]; then
    echo -e "${GREEN}${BOLD}✔ Perfect sync! Your active configurations match the repository exactly. No updates needed.${NC}"
    exit 0
fi

# Print Planned Update Actions
echo -e "${BOLD}Updates to apply to your active ~/.config:${NC}"
for ((i=0; i<${#OPS_TYPE[@]}; i++)); do
    DESC="${OPS_DESC[i]}"
    REL="${OPS_REL[i]}"
    if [[ "$DESC" == "Modified" ]]; then
        echo -e "  ${YELLOW}[Modified]${NC} $REL"
    elif [[ "$DESC" == "Created "* ]]; then
        echo -e "  ${GREEN}[Created ]${NC} $REL"
    else
        echo -e "  ${RED}[Deleted ]${NC} $REL"
    fi
done
echo ""

# Confirmation Prompt
if [ "$DRY_RUN" = false ] && [ "$SKIP_PROMPT" = false ]; then
    read -rp "Would you like to apply these configuration updates? [y/N]: " confirm
    confirm=${confirm:-N}
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Update cancelled by user.${NC}"
        exit 0
    fi
fi

# Execution Phase
echo -e "\n${BOLD}${CYAN}>> Deploying system updates...${NC}"

for ((i=0; i<${#OPS_TYPE[@]}; i++)); do
    OP="${OPS_TYPE[i]}"
    SRC="${OPS_SRC[i]}"
    DST="${OPS_DST[i]}"
    DESC="${OPS_DESC[i]}"
    REL="${OPS_REL[i]}"
    
    if [[ "$DESC" == "Modified" ]]; then
        COLOR="$YELLOW"
    elif [[ "$DESC" == "Created "* ]]; then
        COLOR="$GREEN"
    else
        COLOR="$RED"
    fi

    if [ "$DRY_RUN" = true ]; then
        echo -e "  $COLOR[$DESC]$NC $REL (simulated)"
    else
        echo -e "  $COLOR[$DESC]$NC $REL"
        
        if [[ "$OP" == "copy" ]]; then
            # Ensure target parent directory exists
            mkdir -p "$(dirname "$DST")"
            if [[ -d "$SRC" ]]; then
                cp -rf "$SRC" "$DST"
            else
                cp -f "$SRC" "$DST"
            fi
        elif [[ "$OP" == "delete" ]]; then
            rm -rf "$DST"
        fi
    fi
done

echo -e "\n${GREEN}${BOLD}✔ Update successfully completed! Enjoy your updated Archzenith desktop environment.${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}${BOLD}Note: This was a dry-run. No changes were actually written.${NC}"
fi
