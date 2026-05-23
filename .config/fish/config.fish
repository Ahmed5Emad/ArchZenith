set -g fish_greeting

# Qt & KDE dynamic theme variables
set -gx QT_STYLE_OVERRIDE ""
set -gx QT_QPA_PLATFORMTHEME kde
set -gx QT_QPA_PLATFORM "wayland;xcb"
set -gx QT_WAYLAND_DISABLE_WINDOWDECORATION 1
set -gx XDG_MENU_PREFIX plasma-


if test -f ~/.cache/cwal/sequences
    cat ~/.cache/cwal/sequences
end

if status is-interactive
    # Starship prompt
    starship init fish | source

    # Fastfetch on shell start
    if test -f $HOME/.config/fastfetch/fastfetch.sh
        $HOME/.config/fastfetch/fastfetch.sh
    end

    # Fastfetch refresh function
    function f
        clear
        if test -f $HOME/.config/fastfetch/fastfetch.sh
            $HOME/.config/fastfetch/fastfetch.sh
        end
    end

    # Fastfetch signal handler (equivalent to TRAPUSR1 in zsh)
    function __refresh_fastfetch --on-signal SIGUSR1
        f
    end

    # Keybinding Ctrl+F for Fastfetch refresh
    function fish_user_key_bindings
        bind \cf 'f; commandline -f repaint'
    end

    # Aliases
    alias ls='lsd'
    alias cat='bat'
    alias testcon="$HOME/.config/hypr/scripts/test-connection.sh"
    alias logout='hyprctl dispatch exit'
    alias plugins="$HOME/.config/hypr/maintenance/PLUGINS.sh"
    alias defaults="$HOME/.config/hypr/maintenance/DEFAULTS.sh"
    alias waifu='source $HOME/linux-chat-bot/main.sh (pwd)'
    alias wallpapers="$HOME/.config/hypr/maintenance/WALLPAPERS.sh"
    alias archeclipse='bash -c "$(curl -fsSL https://raw.githubusercontent.com/AymanLyesri/hyprland-conf/refs/heads/master/.config/hypr/maintenance/UPDATE.sh)"'
    alias update_dev='bash -c "$(curl -fsSL https://raw.githubusercontent.com/AymanLyesri/hyprland-conf/refs/heads/dev/.config/hypr/maintenance/UPDATE.sh)" -- dev'

    # Custom Functions
    function code
        /bin/code $argv; and exit
    end

    function v
        /bin/neovide --fork $argv; and exit
    end
end


# Added by Antigravity CLI installer
set -gx PATH "/home/alex/.local/bin" $PATH
