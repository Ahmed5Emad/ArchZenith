import GLib from "gi://GLib";

export const wallpaperPath: string = `${GLib.get_home_dir()}/.config/ags/cache/wallpaper`;

export const gifsPath: string = `${GLib.get_home_dir()}/.config/ags/cache/gifs`;

export const hyprThemeConfPath: string = `${GLib.get_home_dir()}/.config/hypr/theme/theme.conf`;
