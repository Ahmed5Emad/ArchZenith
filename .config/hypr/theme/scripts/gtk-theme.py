#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "cwal"
COLORS_JSON = CACHE_DIR / "colors.json"


def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    return f"#{max(0,min(255,int(r))):02x}{max(0,min(255,int(g))):02x}{max(0,min(255,int(b))):02x}"


def hex_to_rgba(hex_str, alpha=1.0):
    r, g, b = hex_to_rgb(hex_str)
    return f"rgba({r},{g},{b},{alpha})"


def mix_colors(c1, c2, weight):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(
        r1 + (r2 - r1) * weight,
        g1 + (g2 - g1) * weight,
        b1 + (b2 - b1) * weight,
    )


def get_contrast_fg(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    return "#000000" if luminance > 0.45 else "#ffffff"


def parse_colors():
    bg, fg, accent = "#080c0a", "#cdcece", "#499646"
    try:
        if COLORS_JSON.exists():
            data = json.loads(COLORS_JSON.read_text())
            special = data.get("special", {})
            colors = data.get("colors", {})
            bg = special.get("background", bg)
            fg = special.get("foreground", fg)
            accent = colors.get("color4", colors.get("color3", accent))
            print(f"✔ Loaded wallpaper colors. BG={bg}, FG={fg}, Accent={accent}")
    except Exception as e:
        print(f"⚠ Failed to parse colors.json: {e}")

    accent_fg = get_contrast_fg(accent)
    return {
        "bg_color": bg,
        "fg_color": fg,
        "accent_color": accent,
        "accent_fg_color": accent_fg,
        "base_color": mix_colors(bg, fg, 0.08),
        "card_bg_color": mix_colors(bg, fg, 0.12),
        "sidebar_bg_color": mix_colors(bg, fg, 0.05),
        "headerbar_bg_color": mix_colors(bg, fg, 0.03),
        "border_color": mix_colors(bg, fg, 0.18),
        "bg_rgba_025": hex_to_rgba(bg, 0.25),
        "accent_rgba_025": hex_to_rgba(accent, 0.25),
        "accent_rgba_040": hex_to_rgba(accent, 0.40),
        "blue_1": hex_to_rgba(accent, 0.10),
        "blue_2": hex_to_rgba(accent, 0.25),
        "blue_3": accent,
        "blue_4": mix_colors(accent, "#000000", 0.15),
        "blue_5": mix_colors(accent, "#000000", 0.35),
    }


def write_settings_ini(is_dark):
    theme = "adw-gtk3-dark" if is_dark else "adw-gtk3"
    dark = "true" if is_dark else "false"
    for ver in ("gtk-3.0", "gtk-4.0"):
        d = Path.home() / ".config" / ver
        d.mkdir(parents=True, exist_ok=True)
        try:
            (d / "settings.ini").write_text(
                f"[Settings]\ngtk-theme-name = {theme}\ngtk-application-prefer-dark-theme = {dark}\n"
            )
            print(f"✔ Generated {ver} settings.ini")
        except Exception as e:
            print(f"⚠ Failed to write {ver} settings.ini: {e}")


def _overrides(t):
    return f"""@define-color theme_bg_color {t['bg_color']};
@define-color theme_fg_color {t['fg_color']};
@define-color theme_base_color {t['base_color']};
@define-color theme_text_color {t['fg_color']};
@define-color theme_selected_bg_color {t['accent_color']};
@define-color theme_selected_fg_color {t['accent_fg_color']};
@define-color theme_unfocused_selected_bg_color {t['accent_rgba_040']};
@define-color theme_unfocused_selected_fg_color {t['fg_color']};
@define-color selected_bg_color {t['accent_color']};
@define-color selected_fg_color {t['accent_fg_color']};
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
@define-color popover_bg_color {t['card_bg_color']};
@define-color popover_fg_color {t['fg_color']};
@define-color dialog_bg_color {t['bg_color']};
@define-color dialog_fg_color {t['fg_color']};
@define-color accent_color {t['accent_color']};
@define-color accent_bg_color {t['accent_color']};
@define-color accent_fg_color {t['accent_fg_color']};
@define-color theme_accent_color {t['accent_color']};
@define-color theme_accent_bg_color {t['accent_color']};
@define-color theme_accent_fg_color {t['accent_fg_color']};
@define-color borders {t['border_color']};
@define-color unfocused_selected_bg_color {t['accent_rgba_040']};
@define-color unfocused_selected_fg_color {t['fg_color']};
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
treeview.view:selected,treeview.view:selected:focus,treeview.view:selected:hover,
row:selected,listboxrow:selected,.view:selected,.view:selected:focus,
modelbutton:hover,modelbutton:selected {{
  background-color: @theme_selected_bg_color;
  color: @theme_selected_fg_color;
}}
:selected,*:selected,row:selected,listboxrow:selected,
.view:selected,.view:selected:focus,modelbutton:hover,modelbutton:selected {{
  background-color: {t['accent_color']};
  color: {t['accent_fg_color']};
}}
popover modelbutton:hover,popover modelbutton:selected,menuitem:hover,menuitem:selected {{
  background-color: {t['accent_rgba_025']};
  color: {t['fg_color']};
}}
label,text {{ transition: none; }}"""


def write_gtk3_css(t):
    d = Path.home() / ".config" / "gtk-3.0"
    d.mkdir(parents=True, exist_ok=True)
    try:
        (d / "gtk.css").write_text(_overrides(t))
        print(f"✔ Generated GTK3 CSS")
    except Exception as e:
        print(f"⚠ Failed to write GTK3 CSS: {e}")


def write_gtk4_css(t):
    d = Path.home() / ".config" / "gtk-4.0"
    d.mkdir(parents=True, exist_ok=True)
    try:
        (d / "gtk.css").write_text(_overrides(t))
        print(f"✔ Generated GTK4 CSS")
    except Exception as e:
        print(f"⚠ Failed to write GTK4 CSS: {e}")


def main():
    import time

    tokens = parse_colors()
    bg_r, bg_g, bg_b = hex_to_rgb(tokens["bg_color"])
    is_dark = (0.2126 * bg_r + 0.7152 * bg_g + 0.0722 * bg_b) / 255 < 0.5
    theme = "adw-gtk3-dark" if is_dark else "adw-gtk3"

    write_settings_ini(is_dark)
    write_gtk3_css(tokens)
    write_gtk4_css(tokens)

    try:
        temp = "Adwaita" if theme != "Adwaita" else "adw-gtk3"
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", temp], check=True)
        time.sleep(0.3)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", theme], check=True)
        print(f"✔ GTK3/4 reload via gtk-theme → {theme}")
    except Exception as e:
        print(f"⚠ gtk-theme toggle failed: {e}")

    qt6ct = Path.home() / ".config" / "qt6ct" / "qt6ct.conf"
    if qt6ct.exists():
        try:
            qt6ct.touch()
            print(f"✔ Qt6ct reload via touch")
        except Exception as e:
            print(f"⚠ Qt6ct touch failed: {e}")

    try:
        subprocess.run(["ags", "request", "reload-css"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✔ AGS CSS reload requested")
    except Exception as e:
        print(f"⚠ AGS reload-css failed: {e}")

    try:
        subprocess.run(["systemctl", "--user", "restart", "xdg-desktop-portal-gtk"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        print("✔ Restarted xdg-desktop-portal-gtk")
    except Exception as e:
        print(f"⚠ Failed to restart xdg-desktop-portal-gtk: {e}")


if __name__ == "__main__":
    main()
