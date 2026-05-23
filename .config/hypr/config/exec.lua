local home = os.getenv("HOME") or ""
local scriptsDir = home .. "/.config/hypr/scripts"
local themeScriptsDir = home .. "/.config/hypr/theme/scripts"

hl.on("hyprland.start", function()
    -- Sync Hyprland variables to D-Bus and systemd user environment
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP=Hyprland QT_QPA_PLATFORMTHEME=kde QT_STYLE_OVERRIDE=\"\" XDG_MENU_PREFIX=plasma-")
    hl.exec_cmd("systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP QT_QPA_PLATFORMTHEME QT_STYLE_OVERRIDE XDG_MENU_PREFIX")
    -- Restart portals so they inherit the updated clean variables (fixes Kvantum module error in KDE portals)
    hl.exec_cmd("systemctl --user restart xdg-desktop-portal xdg-desktop-portal-hyprland plasma-xdg-desktop-portal-kde xdg-desktop-portal-gtk &")

    hl.exec_cmd("hyprpaper")
    hl.exec_cmd(scriptsDir .. "/compile-run-binaries.sh")
    hl.exec_cmd("systemctl --user start hyprpolkitagent")
    hl.exec_cmd(themeScriptsDir .. "/system-theme.sh apply")
    hl.exec_cmd("nm-applet")
    hl.exec_cmd("wl-paste --watch bash -c \"" .. home .. "/.config/hypr/scripts/clipboard-monitor.sh &\"")
    hl.exec_cmd("blueman-applet")
end)
