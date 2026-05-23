#!/usr/bin/env python3
import json
import math
import subprocess
from pathlib import Path

# Paths
CACHE_DIR = Path.home() / ".cache" / "cwal"
COLORS_JSON = CACHE_DIR / "colors.json"


def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgba(hex_str, alpha=1.0):
    r, g, b = hex_to_rgb(hex_str)
    return f"rgba({r}, {g}, {b}, {alpha})"


def mix_colors(c1, c2, weight):
    """Mix two colors. weight=0.0 means all c1, 1.0 means all c2."""
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    r = r1 + (r2 - r1) * weight
    g = g1 + (g2 - g1) * weight
    b = b1 + (b2 - b1) * weight
    return rgb_to_hex(r, g, b)


def get_contrast_fg(hex_color):
    """Determine whether white or black provides better contrast for a given background hex color."""
    r, g, b = hex_to_rgb(hex_color)
    # Relative luminance sRGB weights
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    return "#000000" if luminance > 0.45 else "#ffffff"


def parse_colors():
    """Extract and generate a full set of design tokens matching cwal wallpaper colors."""
    bg = "#080c0a"
    fg = "#cdcece"
    accent = "#499646"

    try:
        if COLORS_JSON.exists():
            data = json.loads(COLORS_JSON.read_text())
            special = data.get("special", {})
            colors = data.get("colors", {})

            bg = special.get("background", bg)
            fg = special.get("foreground", fg)
            accent = colors.get("color4", colors.get("color3", accent))
            print(f"✔ Successfully loaded wallpaper colors. BG={bg}, FG={fg}, Accent={accent}")
        else:
            print("⚠ colors.json not found, using dark green fallbacks.")
    except Exception as e:
        print(f"⚠ Failed to parse colors.json: {e}")

    accent_fg = get_contrast_fg(accent)

    # Derive dynamic color tokens by blending
    tokens = {
        "bg_color": bg,
        "fg_color": fg,
        "accent_color": accent,
        "accent_fg_color": accent_fg,
        "base_color": mix_colors(bg, fg, 0.08),
        "card_bg_color": mix_colors(bg, fg, 0.12),
        "button_bg_color": mix_colors(bg, fg, 0.15),
        "button_hover_bg_color": mix_colors(bg, fg, 0.22),
        "button_active_bg_color": mix_colors(bg, fg, 0.28),
        "sidebar_bg_color": mix_colors(bg, fg, 0.05),
        "headerbar_bg_color": mix_colors(bg, fg, 0.03),
        "border_color": mix_colors(bg, fg, 0.18),
        "bg_rgba_094": hex_to_rgba(bg, 0.94),
        "bg_rgba_040": hex_to_rgba(bg, 0.40),
        "bg_rgba_060": hex_to_rgba(bg, 0.60),
        "bg_rgba_025": hex_to_rgba(bg, 0.25),
        "bg_rgba_020": hex_to_rgba(bg, 0.20),
        "fg_rgba_005": hex_to_rgba(fg, 0.05),
        "fg_rgba_008": hex_to_rgba(fg, 0.08),
        "fg_rgba_010": hex_to_rgba(fg, 0.10),
        "fg_rgba_040": hex_to_rgba(fg, 0.40),
        "accent_rgba_010": hex_to_rgba(accent, 0.10),
        "accent_rgba_015": hex_to_rgba(accent, 0.15),
        "accent_rgba_020": hex_to_rgba(accent, 0.20),
        "accent_rgba_025": hex_to_rgba(accent, 0.25),
        "accent_rgba_040": hex_to_rgba(accent, 0.40),
        "accent_rgba_050": hex_to_rgba(accent, 0.50),
        "blue_1": hex_to_rgba(accent, 0.10),
        "blue_2": hex_to_rgba(accent, 0.25),
        "blue_3": accent,
        "blue_4": mix_colors(accent, "#000000", 0.15),
        "blue_5": mix_colors(accent, "#000000", 0.35),
    }

    return tokens


def generate_settings_ini(is_dark):
    """Generate settings.ini to force dark or light theme variant appropriately for all GTK apps."""
    prefer_dark = "true" if is_dark else "false"
    
    # GTK 3.0 Settings (Using adw-gtk3-dark as standard dark layout engine to restore gorgeous Libadwaita styling)
    gtk3_theme = "adw-gtk3-dark" if is_dark else "adw-gtk3"
    gtk3_content = f"""[Settings]
gtk-theme-name = {gtk3_theme}
gtk-application-prefer-dark-theme = {prefer_dark}
"""
    gtk3_dir = Path.home() / ".config" / "gtk-3.0"
    gtk3_dir.mkdir(parents=True, exist_ok=True)
    try:
        (gtk3_dir / "settings.ini").write_text(gtk3_content)
        print("✔ Generated GTK3 settings.ini")
    except Exception as e:
        print(f"⚠ Failed to write GTK3 settings.ini: {e}")

    # GTK 4.0 Settings (Sync with adw-gtk3 to maintain visual style integrity)
    gtk4_theme = "adw-gtk3-dark" if is_dark else "adw-gtk3"
    gtk4_content = f"""[Settings]
gtk-theme-name = {gtk4_theme}
gtk-application-prefer-dark-theme = {prefer_dark}
"""
    gtk4_dir = Path.home() / ".config" / "gtk-4.0"
    gtk4_dir.mkdir(parents=True, exist_ok=True)
    try:
        (gtk4_dir / "settings.ini").write_text(gtk4_content)
        print("✔ Generated GTK4 settings.ini")
    except Exception as e:
        print(f"⚠ Failed to write GTK4 settings: {e}")


def generate_gtk3_css(t):
    """Generate a clean, completely custom GTK-3 CSS sheet that overrides
    the default Adwaita engine to match the AGS / Astal widget visual system.
    """
    gtk3_dir = Path.home() / ".config" / "gtk-3.0"
    gtk3_dir.mkdir(parents=True, exist_ok=True)
    gtk3_file = gtk3_dir / "gtk.css"

    gtk3_css = f"""/* ════════════════════════════════════════════════════════════
   DYNAMIC GTK3 CUSTOM DESIGN SYSTEM (AGS & Astal Style)
   Auto-generated by gtk-theme.py — cwal wallpaper colors
   ════════════════════════════════════════════════════════════ */

/* Standard Theme Variables Overrides */
@define-color theme_bg_color {t['bg_color']};
@define-color theme_fg_color {t['fg_color']};
@define-color theme_base_color {t['base_color']};
@define-color theme_text_color {t['fg_color']};
@define-color theme_selected_bg_color {t['accent_color']};
@define-color theme_selected_fg_color {t['accent_fg_color']};
@define-color theme_unfocused_selected_bg_color {t['accent_rgba_040']};
@define-color theme_unfocused_selected_fg_color {t['fg_color']};

@define-color selected_bg_color {t['accent_color']};
@define-color selected_fg_color {t['accent_fg_color']};
@define-color unfocused_selected_bg_color {t['accent_rgba_040']};
@define-color unfocused_selected_fg_color {t['fg_color']};
@define-color bg_color {t['bg_color']};
@define-color fg_color {t['fg_color']};
@define-color base_color {t['base_color']};
@define-color text_color {t['fg_color']};

@define-color view_bg_color {t['base_color']};
@define-color view_fg_color {t['fg_color']};
@define-color window_bg_color {t['bg_color']};
@define-color window_fg_color {t['fg_color']};
@define-color card_bg_color {t['card_bg_color']};
@define-color card_fg_color {t['fg_color']};
@define-color sidebar_bg_color {t['sidebar_bg_color']};
@define-color sidebar_fg_color {t['fg_color']};
@define-color headerbar_bg_color {t['headerbar_bg_color']};
@define-color headerbar_fg_color {t['fg_color']};

@define-color borders {t['border_color']};

/* Reroute GNOME/GTK standard blue highlights to the wallpaper accent color */
@define-color blue_1 {t['blue_1']};
@define-color blue_2 {t['blue_2']};
@define-color blue_3 {t['blue_3']};
@define-color blue_4 {t['blue_4']};
@define-color blue_5 {t['blue_5']};

@define-color accent_color {t['accent_color']};
@define-color accent_bg_color {t['accent_color']};
@define-color accent_fg_color {t['accent_fg_color']};
@define-color theme_accent_color {t['accent_color']};
@define-color theme_accent_bg_color {t['accent_color']};
@define-color theme_accent_fg_color {t['accent_fg_color']};

/* Treeviews / Listbox selection color overrides */
treeview.view:selected,
treeview.view:selected:focus,
treeview.view:selected:hover,
row:selected,
listboxrow:selected,
.view:selected,
.view:selected:focus,
modelbutton:hover,
modelbutton:selected {{
  background-color: @theme_selected_bg_color;
  color: @theme_selected_fg_color;
}}

popover modelbutton:hover,
popover modelbutton:selected,
menuitem:hover,
menuitem:selected {{
  background-color: {t['accent_rgba_025']} !important;
  color: {t['fg_color']} !important;
}}

/* Explicit style for all popovers and their contents / separators / borders to prevent theme bleed-through */
popover,
popover contents,
popover.menu,
popover.menu contents,
popover.background.popover,
.menu-popover,
.tray-popover {{
  border: 1px solid {t['accent_rgba_050']} !important;
  border-radius: 10px !important;
  background-color: {t['card_bg_color']} !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
}}

popover separator,
popover menu separator,
popover .menu-separator,
popover contents separator,
popover contents menu separator,
popover contents .menu-separator,
popover menuitem.separator,
popover menuitem.separator *,
popover.menu separator,
popover.menu .menu-separator {{
  background-color: {t['accent_rgba_040']} !important;
  color: {t['accent_rgba_040']} !important;
  border-color: {t['accent_rgba_040']} !important;
  border: none !important;
  min-height: 1px !important;
}}

/* Disable slow, lagging text and label transitions */
label, text {{
  transition: none !important;
}}
"""
    try:
        gtk3_file.write_text(gtk3_css)
        print(f"✔ Generated premium GTK3 custom overrides in {gtk3_file}")
    except Exception as e:
        print(f"⚠ Failed to write GTK3 overrides: {e}")


def generate_gtk4_css(t):
    """Generate modern, gorgeous GTK-4 Libadwaita custom overrides
    matching the AGS / Astal style.
    """
    gtk4_dir = Path.home() / ".config" / "gtk-4.0"
    gtk4_dir.mkdir(parents=True, exist_ok=True)
    gtk4_file = gtk4_dir / "gtk.css"

    gtk4_css = f"""/* ════════════════════════════════════════════════════════════
   DYNAMIC GTK4 CUSTOM DESIGN SYSTEM (AGS & Astal Style)
   Auto-generated by gtk-theme.py — cwal wallpaper colors
   ════════════════════════════════════════════════════════════ */

/* Standard Libadwaita Colors Overrides */
@define-color window_bg_color {t['bg_color']};
@define-color window_fg_color {t['fg_color']};
@define-color view_bg_color {t['base_color']};
@define-color view_fg_color {t['fg_color']};
@define-color headerbar_bg_color {t['headerbar_bg_color']};
@define-color headerbar_fg_color {t['fg_color']};
@define-color card_bg_color {t['card_bg_color']};
@define-color card_fg_color {t['fg_color']};
@define-color popover_bg_color {t['card_bg_color']};
@define-color popover_fg_color {t['fg_color']};
@define-color dialog_bg_color {t['bg_color']};
@define-color dialog_fg_color {t['fg_color']};
@define-color sidebar_bg_color {t['sidebar_bg_color']};
@define-color sidebar_fg_color {t['fg_color']};

@define-color accent_color {t['accent_color']};
@define-color accent_bg_color {t['accent_color']};
@define-color accent_fg_color {t['accent_fg_color']};

@define-color theme_selected_bg_color {t['accent_color']};
@define-color theme_selected_fg_color {t['accent_fg_color']};
@define-color selected_bg_color {t['accent_color']};
@define-color selected_fg_color {t['accent_fg_color']};

@define-color borders {t['border_color']};

/* Reroute GNOME/GTK standard blue highlights to the wallpaper accent color */
@define-color blue_1 {t['blue_1']};
@define-color blue_2 {t['blue_2']};
@define-color blue_3 {t['blue_3']};
@define-color blue_4 {t['blue_4']};
@define-color blue_5 {t['blue_5']};

:root, * {{
  --accent-color: {t['accent_color']};
  --accent-bg-color: {t['accent_color']};
  --accent-fg-color: {t['accent_fg_color']};
  
  --theme-selected-bg-color: {t['accent_color']};
  --theme-selected-fg-color: {t['accent_fg_color']};
  --selected-bg-color: {t['accent_color']};
  --selected-fg-color: {t['accent_fg_color']};

  --blue-1: {t['blue_1']};
  --blue-2: {t['blue_2']};
  --blue-3: {t['blue_3']};
  --blue-4: {t['blue_4']};
  --blue-5: {t['blue_5']};
}}

/* Selection overrides */
:selected,
*:selected,
row:selected,
listboxrow:selected,
.view:selected,
.view:selected:focus,
modelbutton:hover,
modelbutton:selected {{
  background-color: {t['accent_color']};
  color: {t['accent_fg_color']};
}}

popover modelbutton:hover,
popover modelbutton:selected,
popover button:hover,
popover button:selected,
popover listboxrow:hover,
popover listboxrow:selected {{
  background-color: {t['accent_rgba_025']} !important;
  color: {t['fg_color']} !important;
}}

/* Explicit style for all popovers and their contents / separators / borders to prevent theme bleed-through */
popover,
popover contents,
popover.menu,
popover.menu contents,
popover.background.popover,
.menu-popover,
.tray-popover {{
  border: 1px solid {t['accent_rgba_050']} !important;
  border-radius: 10px !important;
  background-color: {t['card_bg_color']} !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
}}

popover separator,
popover menu separator,
popover .menu-separator,
popover contents separator,
popover contents menu separator,
popover contents .menu-separator,
popover menuitem.separator,
popover menuitem.separator *,
popover.menu separator,
popover.menu .menu-separator {{
  background-color: {t['accent_rgba_040']} !important;
  color: {t['accent_rgba_040']} !important;
  border-color: {t['accent_rgba_040']} !important;
  border: none !important;
  min-height: 1px !important;
}}

/* Disable slow, lagging text and label transitions */
label, text {{
  transition: none !important;
}}
"""
    try:
        gtk4_file.write_text(gtk4_css)
        print(f"✔ Generated premium GTK4 custom overrides in {gtk4_file}")
    except Exception as e:
        print(f"⚠ Failed to write GTK4 overrides: {e}")


def main():
    tokens = parse_colors()
    
    # Calculate background luminance to check if active wallpaper is dark
    bg_r, bg_g, bg_b = hex_to_rgb(tokens["bg_color"])
    bg_luminance = (0.2126 * bg_r + 0.7152 * bg_g + 0.0722 * bg_b) / 255
    is_dark = bg_luminance < 0.5
    
    # First, generate the custom CSS files and settings.ini so they are ready on disk
    generate_settings_ini(is_dark)
    generate_gtk3_css(tokens)
    generate_gtk4_css(tokens)
    
    # Then, perform the gsettings theme toggle to trigger hot-reloading for running GTK apps
    theme_name = "adw-gtk3-dark" if is_dark else "adw-gtk3"
    try:
        import time
        temp_theme = "Adwaita" if theme_name != "Adwaita" else "adw-gtk3"
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", temp_theme], check=True)
        time.sleep(0.2)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", theme_name], check=True)
        print(f"✔ Dynamic system GTK theme set via gsettings to {theme_name} (hot-reloaded)")
    except Exception as e:
        print(f"⚠ Failed to set gsettings theme dynamically: {e}")

    # Request the running AGS instance to recompile and apply the new CSS dynamically (seamless!)
    try:
        subprocess.run(["ags", "request", "reload-css"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✔ Requested running AGS instance to reload CSS dynamically (seamless)")
    except Exception as e:
        print(f"⚠ Failed to request AGS CSS reload: {e}")


if __name__ == "__main__":
    main()
