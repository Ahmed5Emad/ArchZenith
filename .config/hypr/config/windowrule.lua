hl.window_rule({
    match = { class = "^(polkit-gnome-authentication-agent-1)$" },
    float = true,
})

hl.window_rule({
    match = { class = "^(nm-connection-editor|blueman-manager)$" },
    float = true,
})

hl.window_rule({
    match = { class = "^(swayimg|Viewnior|pavucontrol|org.pulseaudio.pavucontrol)$" },
    float = true,
    size = "700 500",
})

hl.window_rule({
    match = { class = "^(nwg-look|qt5ct|mpv|zoom|Rofi|feh)$" },
    float = true,
})

hl.window_rule({
    match = { class = "^(Rofi|pavucontrol|blueman-manager)$" },
    pin = true,
})

hl.window_rule({
    match = { title = "Picture-in-Picture" },
    float = true,
    pin = true,
    move = "100%-w-14 100%-w-7",
})

hl.window_rule({
    match = { class = "preview-image" },
    float = true,
    move = "cursor -50% -50%",
})

hl.window_rule({
    match = { title = "booru-image" },
    float = true,
    move = "cursor -50% -50%",
})

hl.window_rule({
    match = { class = "^(steam_app_\\d+)$" },
    opacity = "1 override 1 override",
})

hl.window_rule({
    match = { class = "^(.+\\.exe)$" },
    opacity = "1 override 1 override",
})

hl.window_rule({
    match = { class = "^(Emulator)$" },
    opacity = "1 override 1 override",
})

hl.window_rule({
    match = { class = "^(grass)$" },
    workspace = "9 silent",
})

hl.window_rule({
    match = { class = "^(xdg-desktop-portal-gtk)$" },
    float = true,
    size = "800 600",
    center = true,
})

hl.window_rule({
    match = { class = "^(zen|firefox|librewolf|thorium|chromium|google-chrome|brave-browser|vivaldi)$", title = "^Library$" },
    float = true,
    size = "800 600",
    center = true,
})

hl.window_rule({
    match = { class = "^(Spotify)$" },
    workspace = "4 silent",
})
