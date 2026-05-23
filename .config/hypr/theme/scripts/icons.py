#!/usr/bin/env python3
import os
import json
import math
import colorsys
import subprocess
import shutil
from pathlib import Path

# Paths
CACHE_DIR = Path.home() / ".cache" / "cwal"
COLORS_JSON = CACHE_DIR / "colors.json"
KDEGLOBALS = Path.home() / ".config" / "kdeglobals"

# Pre-defined anchor colors for Tela variants (RGB coordinates)
TELA_ANCHORS = {
    "red": (220, 53, 69),      # Crimson / Red
    "blue": (0, 0, 255),       # Deep / Royal Blue (Shifted to 240° to leave room for nord)
    "green": (40, 167, 69),    # Forest / Emerald Green
    "purple": (111, 66, 193),  # Deep Purple
    "pink": (232, 62, 140),    # Magenta / Pink
    "orange": (253, 126, 20),  # Tangerine Orange
    "yellow": (255, 193, 7),   # Sunshine Yellow
    "brown": (139, 69, 19),    # Earthy Brown
    "nord": (80, 180, 220),    # Teal / Cyan-Blue (Shifted to capture storm colors)
    "dracula": (189, 147, 249),# Dracula Pastel Purple
    "grey": (108, 117, 125),   # Cool Slate / Grey
    "black": (40, 40, 40),     # Dark / Black
    "manjaro": (50, 150, 100), # Manjaro Green
    "ubuntu": (230, 70, 30),   # Ubuntu Orange
}


def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))


def hex_to_rgba(hex_str, alpha=1.0):
    """Convert hex color to rgba() string for 100% GTK CSS compatibility."""
    hex_str = hex_str.lstrip('#')
    r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# Pre-computed hue angles for colored TELA_ANCHORS (deg, 0-360)
# "grey" is excluded from hue matching — it only triggers on saturation/value threshold
_TELA_HUES = {
    name: colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[0] * 360
    for name, (r, g, b) in TELA_ANCHORS.items()
    if name != "grey"
}


def get_closest_variant(target_rgb):
    tr, tg, tb = target_rgb

    # Convert target to HSV to extract hue and check saturation
    th, ts, tv = colorsys.rgb_to_hsv(tr / 255, tg / 255, tb / 255)
    th_deg = th * 360

    # Grey only triggers for desaturated or very dark colors
    if ts < 0.12 or tv < 0.15:
        return "grey"

    # Find closest by hue angle (shortest path around the color wheel)
    min_distance = float('inf')
    best_match = "grey"

    for name, ah_deg in _TELA_HUES.items():
        d = abs(th_deg - ah_deg)
        if d > 180:
            d = 360 - d
        if d < min_distance:
            min_distance = d
            best_match = name

    return best_match


def is_dark_mode():
    try:
        # Check current GTK preferred color scheme
        res = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True, text=True, check=True
        )
        # If 'light' is in the GSettings output, it's light mode. Otherwise, it defaults to dark mode.
        return "light" not in res.stdout.lower()
    except Exception:
        # Fallback default
        return True


def apply_kde_window_colors(hex_color, dark):
    mode_flag = "-d" if dark else "-l"
    try:
        # Check standard PATH first
        bin_path = shutil.which("kde-material-you-colors")

        # Check ~/.local/bin fallback explicitly
        if not bin_path:
            local_bin = Path.home() / ".local" / "bin" / "kde-material-you-colors"
            if local_bin.exists() and os.access(local_bin, os.X_OK):
                bin_path = str(local_bin)

        if bin_path:
            print(f"✔ Running {bin_path} with color {hex_color} in background...")
            # We override the seed color to match our active cwal theme color exactly
            # We run it in background because it is designed to run as an infinite monitoring daemon.
            proc = subprocess.Popen(
                [bin_path, mode_flag, "--color", hex_color],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            import time
            time.sleep(2.5)  # Give it time to fully apply the theme
            proc.terminate()
            try:
                proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                proc.kill()

            print("✔ Dynamic window colors applied to KDE/Qt apps.")
        else:
            print("⚠ kde-material-you-colors binary is not found in PATH or ~/.local/bin/ yet. Skipping window color generation.")
    except Exception as e:
        print(f"⚠ Failed to apply dynamic KDE window colors: {e}")


def apply_gtk_icon_theme(theme_name):
    try:
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", theme_name],
            check=True
        )
        print(f"✔ Applied GTK icon theme: {theme_name}")
    except Exception as e:
        print(f"⚠ Failed to set GTK icon theme: {e}")


def apply_kde_icon_theme(theme_name):
    if not KDEGLOBALS.exists():
        print("⚠ kdeglobals file not found, skipping KDE theme sync.")
        return

    try:
        content = KDEGLOBALS.read_text()
        lines = content.splitlines()
        new_lines = []
        in_icons_section = False
        theme_replaced = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[Icons]"):
                in_icons_section = True
                new_lines.append(line)
                continue
            elif stripped.startswith("[") and stripped.endswith("]"):
                in_icons_section = False

            if in_icons_section and stripped.startswith("Theme="):
                new_lines.append(f"Theme={theme_name}")
                theme_replaced = True
            else:
                new_lines.append(line)

        # If the [Icons] section exists but doesn't have Theme=, append it
        if in_icons_section and not theme_replaced:
            new_lines.append(f"Theme={theme_name}")
            theme_replaced = True

        KDEGLOBALS.write_text("\n".join(new_lines) + "\n")
        print(f"✔ Applied KDE icon theme in kdeglobals: {theme_name}")
    except Exception as e:
        print(f"⚠ Failed to update kdeglobals: {e}")





def get_winning_category_color(palette):
    """Cluster colors by hue and pick the one from the highest-mass cluster."""
    colors = []
    for i in range(16):
        c = palette.get(f"color{i}", "#000000")
        r, g, b = hex_to_rgb(c)
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        # Filter neutral colors
        if s > 0.15 and v > 0.2:
            colors.append({'hex': c, 'h': h * 360, 'salience': s * v})

    if not colors:
        return "#808080"

    # Bucket colors by hue (20 degree buckets: 0-20, 20-40, ..., 340-360)
    buckets = {}
    for c in colors:
        bucket_id = int(c['h'] // 20)
        if bucket_id not in buckets:
            buckets[bucket_id] = {'mass': 0.0, 'colors': []}
        buckets[bucket_id]['mass'] += c['salience']
        buckets[bucket_id]['colors'].append(c)

    # Pick the winning bucket (highest total mass)
    best_bucket_id = max(buckets, key=lambda k: buckets[k]['mass'])
    best_bucket = buckets[best_bucket_id]

    # Pick the color with the highest salience *within* that winning bucket
    return max(best_bucket['colors'], key=lambda x: x['salience'])['hex']


def main():
    if not COLORS_JSON.exists():
        print(f"Error: cwal color cache not found at {COLORS_JSON}")
        return

    try:
        data = json.loads(COLORS_JSON.read_text())
        # Pick the most vibrant (salient) color from the palette
        hex_color = get_winning_category_color(data.get("colors", {}))
    except Exception as e:
        print(f"Error parsing colors.json: {e}")
        return

    rgb = hex_to_rgb(hex_color)
    variant = get_closest_variant(rgb)

    # Check if system is dark or light
    dark = is_dark_mode()
    suffix = "-dark" if dark else ""

    # Formulate theme name (e.g. Tela-nord-dark or Tela-red-dark)
    target_theme = f"Tela-{variant}{suffix}"

    # Fallback to standard "Tela-dark" if specific variant folder doesn't exist
    icon_paths = [
        Path.home() / ".local" / "share" / "icons" / target_theme,
        Path("/usr/share/icons") / target_theme
    ]

    if not any(p.exists() for p in icon_paths):
        print(f"⚠ Derived theme '{target_theme}' not found in icon directories. Falling back to default 'Tela-dark'.")
        target_theme = "Tela-dark" if dark else "Tela"

    print(f"Wallpaper color: {hex_color} -> Mapped to Tela Variant: {variant}")

    # Generate KDE window colors via Material You (contrast-compliant accents)
    apply_kde_window_colors(hex_color, dark)

    # Apply icons (ensures our custom Tela color-matched icons aren't overwritten)
    apply_gtk_icon_theme(target_theme)
    apply_kde_icon_theme(target_theme)


if __name__ == "__main__":
    main()
