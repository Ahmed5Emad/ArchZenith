local function get_native_browser()
    local handle = io.popen("xdg-settings get default-web-browser 2>/dev/null")
    if not handle then
        return "zen-browser"
    end

    local result = handle:read("*a"):gsub("%s+", "")
    handle:close()

    if not result or result == "" then
        return "zen-browser"
    end

    local home = os.getenv("HOME") or ""
    local desktop_dirs = {
        home .. "/.local/share/applications/",
        "/usr/share/applications/",
        "/usr/local/share/applications/",
    }

    -- Look up the desktop file to extract the real Exec command
    for _, dir in ipairs(desktop_dirs) do
        local desktop_file = io.open(dir .. result, "r")
        if desktop_file then
            for line in desktop_file:lines() do
                local exec = line:match("^Exec%s*=%s*(.+)")
                if exec then
                    desktop_file:close()
                    -- Strip %-parameters (e.g., %f, %u, %F, %U)
                    exec = exec:gsub("%%[%w]+", "")
                    -- Strip trailing whitespace
                    exec = exec:gsub("%s+$", "")
                    return exec
                end
            end
            desktop_file:close()
        end
    end

    -- Fallback: strip .desktop and try common name mappings
    local app_id = result:gsub("%.desktop$", "")
    local known = {
        zen = "zen-browser",
        ["zen-browser"] = "zen-browser",
    }
    return known[app_id] or app_id
end

local browser = get_native_browser()

hl.on("hyprland.start", function()
    hl.exec_cmd(browser)
end)

hl.window_rule({
    match = { title = "^(Zen Browser)$" },
    workspace = "2 silent",
})

return browser
