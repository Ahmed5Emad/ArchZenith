<div align="center">

```
    ___               __                      _ __  __  
   /   |  ___________/ /_  ________  ____  (_) /_/ /_ 
  / /| | / ___/ ___/ __ \/_  /_  / / __ \/ / __/ __ \
 / ___ |/ /  / /__/ / / / / /_/ /_/ / / / / /_/ / / / 
/_/  |_/_/   \___/_/ /_/ /___/___/_/ /_/_/\__/_/ /_/  
```

**A premium, performance-focused Arch Linux + Hyprland desktop environment.**  
*Customized, extended, and polished fork of the beautiful upstream [ArchEclipse](https://github.com/AymanLyesri/ArchEclipse).*

[![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?style=for-the-badge&logo=arch-linux&logoColor=white)](https://archlinux.org/)
[![Hyprland](https://img.shields.io/badge/Hyprland-58E1FF?style=for-the-badge&logo=wayland&logoColor=black)](https://hyprland.org/)
[![AGS](https://img.shields.io/badge/AGS-v2_Astal-FF79C6?style=for-the-badge)](https://github.com/Aylur/ags)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

</div>

---

## 📸 Screenshots

> [!NOTE]
> Below are showcase screenshots of Archzenith in action, demonstrating its modern widget engine and dynamic theming features.

### Upstream Showcase (Overview)
*Original design layout and full widget panel setup.*
<div align="center">

![Overview](https://raw.githubusercontent.com/AymanLyesri/ArchEclipse/refs/heads/master/.github/assets/overview.png)

</div>

---

### New Screenshots

#### 🌅 Crimson Sunrise Theme
*A warm, sleek dark-mode configuration showcasing clean panels, workspace-aware widget indicators, and beautiful spacing.*

<div align="center">

![Crimson Sunrise](./Screenshots/crimson%20Sunrise.webp)

</div>

#### 🟢 Launcher & Widget Panel (Green Theme)
*Showing off the premium search drawer launcher, high-fidelity blur filters, and fluid color integration matching the dynamic wallpaper system.*

<div align="center">

![Launcher in Green](./Screenshots/luancher%20in%20grean.webp)

</div>

---

## ✨ Features

| Category | Component & Project Links | Description |
| :--- | :--- | :--- |
| 🪟 **Window Manager** | [Hyprland](https://hyprland.org/) | Wayland-based, incredibly fluid dynamic tiling window manager |
| 🎨 **Widgets & Bar** | [Aylur's GTK Shell (AGS v2 / Astal)](https://github.com/Aylur/ags) | Custom premium desktop panels, launcher, and unified control hub |
| 🐚 **Shell** | [Fish](https://fishshell.com/) + [Starship](https://starship.rs/) | Fast interactive shell with custom prompt styling and context syntax |
| 🎵 **Audio Backend** | [Pipewire](https://pipewire.org/) + [Pamixer](https://github.com/cdemoulins/pamixer) | Modern low-latency pipeline with granular terminal level controllers |
| 📺 **Wallpaper** | [Hyprpaper](https://github.com/hyprwm/hyprpaper) | Lightweight compositor companion featuring workspace-aware controls |
| 🔒 **Lock Screen** | [Hyprlock](https://github.com/hyprwm/hyprlock) | Modern, secure, and fully customized lock system |
| 🎨 **Color Engine** | [kde-material-you-colors](https://github.com/luisbocanegra/kde-material-you-colors) | Dynamically tailors UI schemes across GTK, Qt, and core modules |
| 📂 **File Manager** | [Dolphin](https://apps.kde.org/dolphin/) | Fast file navigation with uniform Qt6/GTK application styling |
| 🖥️ **Sys Monitor** | [Btop](https://github.com/aristocratos/btop) | Premium terminal-based resource viewer |
| 🔐 **Bluetooth** | [Blueman](https://github.com/blueman-project/blueman) | Complete Bluetooth adapter daemon & device manager interface |
| 📡 **Network** | [NetworkManager](https://networkmanager.dev/) + `nm-applet` | Robust network daemon with lightweight panel indicator applet |
| 🔑 **Auth Agent** | [Hyprpolkitagent](https://github.com/hyprwm/hyprpolkitagent) | Native Hyprland policy kit integration framework |
| ✏️ **Typography** | JetBrains Mono Nerd Font | Outstanding design typography coupled with high-density Noto Emoji |
| 🖱️ **Cursors** | [Phinger Cursors](https://github.com/phisch/phinger-cursors) | Modern, highly visible crosshair & standard icon sets |

---

## 📦 Modular Package Sections

The premium installer breaks setup down into **7 modular sections**, allowing you to customize your setup interactively:

1. **Desktop Shell & Widgets** — AGS widget architecture, Astal metadata, and SASS/CSS compilers.
2. **Window Manager & Compositor** — Hyprland core compositor, hyprlock, hyprpaper, cursors, and auth agent.
3. **Shell & System Utilities** — Fish shell, Starship prompt, btop, fastfetch, jq, bat, socat, and custom plugins.
4. **Hardware & Media Control** — Pipewire audio backend, Blueman bluetooth suite, NetworkManager integration, and device keys.
5. **Media Playback** — VLC media player layers.
6. **Look & Feel Theme Layers** — SDDM themes, JetBrains font, material-you core engine, and Qt5/Qt6 compatibility.
7. **Compilation Tools** — Essential build utilities including cmake, meson, gcc, cpio, and helper bundles.

---

## ⚙️ Installation

### Prerequisites

- A fresh or existing **Arch Linux** installation.
- A functional terminal base environment (e.g., standard tty shell with internet).
- `git` installed (`sudo pacman -S git`).

### Interactive Setup

Clone the project repository and run the automated interactive shell installer:

```bash
git clone https://github.com/Ahmed5Emad/Archzenith
cd Archzenith
chmod +x install.sh
./install.sh
```

### Installation Pipeline

```
┌──────────────────────────────────────────────────────────┐
│ 1. sudo Check & Privilege Preservation                   │
└───────────────────────────┬──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│ 2. Smart Backup (~/.config -> ~/.config_bak_<timestamp>)  │
└───────────────────────────┬──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│ 3. AUR Helper Validation (Installs 'yay' if missing)     │
└───────────────────────────┬──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│ 4. Interactive Package Selection (7 Modular Sections)    │
└───────────────────────────┬──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│ 5. Optional Flat Icon Set Deploy (Tela Icon Theme)       │
└───────────────────────────┬──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│ 6. Launch & Enjoy! (Log into your new Hyprland session)  │
└──────────────────────────────────────────────────────────┘
```

---

## ⌨️ Key Bindings Cheat Sheet

### 🗔 Window Management
| Keybind | Action |
| :--- | :--- |
| `SUPER + Q` | Close active window |
| `SUPER + F` | Toggle window fullscreen state |
| `SUPER + S` | Toggle window maximize state |
| `SUPER + Space` | Toggle window float mode |
| `SUPER + [1–0]` | Switch to active workspaces `1` through `10` |

### 🚀 Application Launchers
| Keybind | Action |
| :--- | :--- |
| `SUPER + T` | Open terminal emulator (Kitty) |
| `SUPER + W` | Open web browser (Zen) |
| `SUPER + E` | Open file manager (Dolphin) |
| `SUPER + A` | Open unified AGS applications drawer |

### 🎛️ Desktop & Widget Controls
| Keybind | Action |
| :--- | :--- |
| `SUPER + B` | Live refresh the status bar and widgets |
| `SUPER + M` | Toggle status media panel controls |
| `SUPER + R` | Toggle right side information panel drawer |
| `SUPER + L` | Toggle left side control center drawer |
| `SUPER + SHIFT + W` | Launch interactive wallpaper switcher utility |

### 🛠️ System & Session Actions
| Keybind | Action |
| :--- | :--- |
| `SUPER + SHIFT + S` | Capture custom screen region screenshot |
| `Print` | Capture full-screen screenshot |
| `SUPER + SHIFT + R` | Start screen recording |
| `SUPER + P` | Open `btop` system monitor on workspace `5` |
| `SUPER + SHIFT + Escape` | Lock desktop session (Hyprlock) |
| `SUPER + CTRL + Escape` | Suspend system session |
| `SUPER + Escape` | Toggle user options panel (Logout / Power Actions) |

---

## 📁 Configuration Directory Structure

Here is a map of the deployed files and where to make customizations:

```
Archzenith/
├── install.sh             # High-fidelity shell installer script
├── Screenshots/           # Theme visual assets
└── .config/
    ├── ags/               # Premium desktop widgets & bars (TypeScript + SCSS)
    ├── cava/              # Desktop audio spectrum visualizer profiles
    ├── fastfetch/         # Modern console system specs card
    ├── fish/              # Interactive modern terminal shell configuration
    ├── hypr/              # Core Hyprland configuration framework
    │   ├── config/        # Keybinds, animations, and desktop decorations
    │   ├── scripts/       # Control utilities (screenshooter, locker, panels)
    │   ├── theme/         # Color scheme application engines
    │   └── pacman/        # Clean target lists & check script suites
    ├── kitty/             # GPU-accelerated terminal profiles
    ├── pipewire/          # Complete audio subsystem settings
    └── starship.toml      # Universal shell prompt style configurations
```

---

## 🔄 System Updates

Archzenith includes a premium automated update utility (`update.sh`) so that you can easily pull down the latest repository updates and safely deploy them to your system.

### Features
* 📥 **Git Synchronized**: Automatically pulls the latest commits from GitHub.
* 🔍 **Precise Change Previews**: Scans your active `~/.config` against the new updates and presents a color-coded modification list.
* 🛡️ **Cache & Log Safe**: Only applies files tracked by Archzenith. It **never** touches or deletes your personal app caches (`ags/cache/`), logs (`ags/logs/`), or unrelated local settings!

### How to Update

Navigate to your local repository clone and execute the updater:
```bash
./update.sh
```

To run a simulation and preview updates without copying any files:
```bash
./update.sh --dry-run
```

---

## 🙏 Credits

This configuration is based on and heavily inspired by the outstanding work of:

> **[AymanLyesri](https://github.com/AymanLyesri)** — Original author of [ArchEclipse](https://github.com/AymanLyesri/ArchEclipse)  
> *Highly polished, performance-focused Arch Linux + Hyprland dotfiles with dynamic theming, custom widgets, and a fast, modern workflow.*

All credit for the original AGS widget architecture, Hyprland configuration setup, and core utility scripts belongs to him. Archzenith is a personalized fork with optimized package targets, updated components, and a custom interactive installation wrapper.

---

## 📝 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more details.

---

<div align="center">

*Made with ❤️ on Arch Linux*

⭐ Star the repository if you enjoy using it!

</div>
