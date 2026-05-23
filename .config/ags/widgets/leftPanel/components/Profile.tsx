import { Gtk } from "ags/gtk4";
import { createState, For, With } from "ags";
import { execAsync, exec } from "ags/process";
import { notify } from "../../../utils/notification";
import GLib from "gi://GLib";
import Gio from "gi://Gio";
import Pango from "gi://Pango";
import { createPoll } from "ags/time";

import Hyprland from "gi://AstalHyprland";
import Picture from "../../Picture";
import { globalSettings } from "../../../variables";
const hyprland = Hyprland.get_default();

// Profile picture path settings
const homePfpPath = GLib.getenv("HOME") + "/.face.icon";
const pfpPath = Gio.File.new_for_path(homePfpPath).query_exists(null)
  ? homePfpPath
  : `${GLib.get_home_dir()}/.config/ags/assets/userpanel/archzenith_default_pfp.jpg`;

const username = GLib.get_user_name();
const desktopEnv = GLib.getenv("XDG_CURRENT_DESKTOP") || "Unknown DE";
const namePath = GLib.get_home_dir() + "/.config/ags/cache/settings/display_name.txt";

const getDisplayName = () => {
  try {
    const file = Gio.File.new_for_path(namePath);
    if (file.query_exists(null)) {
      const [, content] = file.load_contents(null);
      const name = new TextDecoder("utf-8").decode(content).trim();
      if (name) return name;
    }
  } catch (e) {
    console.error("Failed to read display name:", e);
  }
  return GLib.get_user_name();
};

const uptime = createPoll("", 60000, "uptime -p"); // every minute

// General information section (version, github link, etc.)
const GeneralInfo = () => {
  const [currentVersion, setCurrentVersion] = createState("");
  const [remoteVersion, setRemoteVersion] = createState("");
  const [isCheckingVersion, setIsCheckingVersion] = createState(true);
  const [isUpdating, setIsUpdating] = createState(false);
  const [updateStatus, setUpdateStatus] = createState("");

  const configDir = GLib.getenv("HOME") + "/.config/ags";

  const checkVersions = async () => {
    setIsCheckingVersion(true);
    try {
      // Get current local commit
      const localHash = exec(
        `git -C ${configDir} rev-parse --short HEAD`,
      ).trim();
      setCurrentVersion(localHash);

      // Fetch and get remote commit
      await execAsync(`git -C ${configDir} fetch origin master`);
      const remoteHash = await execAsync(
        `git -C ${configDir} rev-parse --short origin/master`,
      );
      setRemoteVersion(remoteHash.trim());
      setUpdateStatus("");
    } catch (e) {
      console.error("Failed to check versions:", e);
      setCurrentVersion("Unknown");
      setRemoteVersion("Unknown");
      setUpdateStatus("");
    } finally {
      setIsCheckingVersion(false);
    }
  };

  const updateVersion = async () => {
    try {
      hyprland.dispatch("exec", "kitty fish -ic 'clear; archzenith'");
    } catch (e) {
      console.error("Failed to launch update command:", e);
      const errorMessage = (e instanceof Error ? e.message : String(e))
        .replace(/['"\\`\n\r]/g, " ")
        .replace(/\s+/g, " ")
        .trim();
      notify({
        summary: "Launch Error",
        body: errorMessage || "Could not open kitty with archzenith.",
      });
    }
  };

  const isOutdated = () => {
    return (
      currentVersion() &&
      remoteVersion() &&
      currentVersion() !== remoteVersion() &&
      currentVersion() !== "Unknown"
    );
  };

  const links = [
    {
      description: "GitHub Repository",
      url: "https://github.com/Ahmed5Emad/Archzenith",
      icon: "",
    },
    {
      description: "Issues Tracker",
      url: "https://github.com/Ahmed5Emad/Archzenith/issues",
      icon: "",
    },
    {
      description: "Discord Community",
      url: "https://discord.gg/fMGt4vH6s5",
      icon: "",
    },
  ];

  return (
    <box class={"info"} orientation={Gtk.Orientation.VERTICAL} spacing={10}>
      <box spacing={10} halign={Gtk.Align.CENTER}>
        <label class={"config-title"} label="ArchZenith" />
        {/* github stars */}
        <label
          class={"config-stars"}
          $={(self) => {
            execAsync(
              `bash -c "curl -s https://api.github.com/repos/Ahmed5Emad/Archzenith | jq '.stargazers_count'"`,
            ).then((result) => {
              const stars = result.trim();
              if (stars && stars !== "null") {
                self.label = `  ${stars}`;
              } else {
                self.label = `  0`;
              }
            }).catch(() => {
              self.label = `  0`;
            });
          }}
        />
      </box>
      <box spacing={10} halign={Gtk.Align.CENTER}>
        {links.map((link) => (
          <button
            class={"link-button"}
            onClicked={() => execAsync(`xdg-open "${link.url}"`)}
            tooltipText={link.description}
          >
            <label label={link.icon} />
          </button>
        ))}
      </box>
      <box
        class={"section version-section"}
        orientation={Gtk.Orientation.VERTICAL}
        $={() => {
          checkVersions();
        }}
      >
        <With value={isCheckingVersion}>
          {(isChecking) =>
            isChecking ? (
              <label
                class={"version-status loading"}
                label="🔄 Checking for updates..."
              />
            ) : (
              <box
                class={"version-container"}
                orientation={Gtk.Orientation.VERTICAL}
                spacing={8}
              >
                {/* Version Info Row */}
                {remoteVersion() && (
                  <box spacing={10} halign={Gtk.Align.CENTER}>
                    <box
                      orientation={Gtk.Orientation.VERTICAL}
                      spacing={5}
                      hexpand
                    >
                      <label class={"version-label"} label="Current Version" />
                      <label
                        class={"version-value"}
                        label={currentVersion() || "Unknown"}
                      />
                    </box>

                    <box
                      orientation={Gtk.Orientation.VERTICAL}
                      spacing={5}
                      hexpand
                    >
                      <label class={"version-label"} label="Latest Version" />
                      <label class={"version-value"} label={remoteVersion()} />
                    </box>
                  </box>
                )}

                {/* Status Row */}
                <box spacing={8}>
                  {isOutdated() ? (
                    <box spacing={10} halign={Gtk.Align.CENTER} hexpand>
                      <label
                        class={"version-status outdated"}
                        label="⚠️ Update available"
                        hexpand
                      />
                      <button
                        class={`update-button ${isUpdating() ? "updating" : ""}`}
                        sensitive={!isUpdating()}
                        onClicked={updateVersion}
                        tooltipText="Click to update to the latest version"
                      >
                        <box spacing={5}>
                          {isUpdating() && (
                            <label label="⟳" class={"spinner"} />
                          )}
                          {!isUpdating() && <label label="⬇" />}
                          <label
                            label={isUpdating() ? "Updating..." : "Update"}
                          />
                        </box>
                      </button>
                    </box>
                  ) : (
                    <box spacing={10} halign={Gtk.Align.CENTER} hexpand>
                      <label
                        class={"version-status uptodate"}
                        label={`✓ Up to date${updateStatus() ? ` - ${updateStatus()}` : ""}`}
                        hexpand
                      />
                      {/* Manual update check button */}
                      {!isUpdating() && (
                        <button
                          class="update-button secondary"
                          onClicked={checkVersions}
                          tooltipText="Manually check for updates"
                        >
                          <box spacing={5}>
                            <label label="" />
                            <label label="Check Update" />
                          </box>
                        </button>
                      )}
                    </box>
                  )}
                </box>
              </box>
            )
          }
        </With>
      </box>
    </box>
  );
};

export default () => {
  const [displayName, setDisplayName] = createState(getDisplayName());
  const [osAge, setOsAge] = createState("Calculating OS age...");
  const [sysStats, setSysStats] = createState<any>({
    os: "Arch Linux",
    kernel: "Linux",
    packages: "Loading...",
    shell: "fish",
    cpu: "Loading...",
    gpu: "Loading...",
    memory: "Loading..."
  });

  const changeDisplayName = async () => {
    try {
      const current = displayName();
      const newName = await execAsync(
        `zenity --entry --title="Change Display Name" --text="Enter your new display name:" --entry-text=${JSON.stringify(current)}`
      );
      if (newName && newName.trim() !== "") {
        const cleanName = newName.trim();
        const dir = Gio.File.new_for_path(GLib.get_home_dir() + "/.config/ags/cache/settings");
        if (!dir.query_exists(null)) {
          dir.make_directory_with_parents(null);
        }
        await execAsync(`bash -c "echo -n ${JSON.stringify(cleanName)} > ${JSON.stringify(namePath)}"`);
        setDisplayName(cleanName);
        notify({
          summary: "Profile Updated",
          body: `Display name changed to ${cleanName}!`,
        });
      }
    } catch (err) {
      const errorStr = String(err);
      if (errorStr.includes("exit status 1")) return; // User cancelled
      notify({
        summary: "Error",
        body: errorStr,
      });
    }
  };

  const calculateOSAge = async () => {
    try {
      const birthStr = await execAsync("stat -c %w /");
      const birthDate = new Date(birthStr.trim().split(" ")[0]);
      const now = new Date();
      const diffTime = Math.abs(now.getTime() - birthDate.getTime());
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
      
      const years = Math.floor(diffDays / 365);
      const months = Math.floor((diffDays % 365) / 30);
      const days = (diffDays % 365) % 30;

      let ageString = "";
      if (years > 0) ageString += `${years} yr${years > 1 ? "s" : ""}, `;
      if (months > 0) ageString += `${months} mo${months > 1 ? "s" : ""}, `;
      ageString += `${days} day${days > 1 ? "s" : ""}`;

      setOsAge(ageString);
    } catch (e) {
      console.error("Failed to calculate OS age:", e);
      setOsAge("Unknown");
    }
  };

  const loadFastfetchData = async () => {
    try {
      const jsonStr = await execAsync("fastfetch --format json");
      if (!jsonStr || jsonStr.trim() === "") return;
      const data = JSON.parse(jsonStr.trim());
      
      const stats: any = {};
      data.forEach((item: any) => {
        if (!item || !item.result) return;
        
        if (item.type === "OS") {
          stats.os = item.result.prettyName || item.result.name || "Arch Linux";
        } else if (item.type === "Kernel") {
          stats.kernel = item.result.release || "Linux";
        } else if (item.type === "Packages") {
          stats.packages = item.result.all || "Unknown";
        } else if (item.type === "Shell") {
          const shellPath = item.result.path || item.result.exePath || "fish";
          stats.shell = shellPath.split("/").pop() || "fish";
        } else if (item.type === "CPU") {
          const cpuName = item.result.cpu || "Unknown CPU";
          stats.cpu = cpuName.replace(/\(R\)|\(TM\)/g, "").trim();
        } else if (item.type === "GPU") {
          const gpuList = Array.isArray(item.result) ? item.result : [item.result];
          stats.gpu = gpuList
            .map((g: any) => {
              const gName = g.name || "Unknown GPU";
              return gName.replace("GeForce ", "").replace("Radeon ", "").trim();
            })
            .join(", ");
        } else if (item.type === "Memory") {
          const total = item.result.total || 0;
          const used = item.result.used || 0;
          const totalGB = (total / (1024 * 1024 * 1024)).toFixed(1);
          const usedGB = (used / (1024 * 1024 * 1024)).toFixed(1);
          stats.memory = `${usedGB} GiB / ${totalGB} GiB`;
        }
      });
      setSysStats({ ...sysStats(), ...stats });
    } catch (e) {
      console.error("Failed to load fastfetch data:", e);
    }
  };

  const initData = () => {
    calculateOSAge();
    loadFastfetchData();
  };

  const UserProfileCard = () => {
    return (
      <box class="user-profile-card" hexpand orientation={Gtk.Orientation.VERTICAL} spacing={10} $={initData}>
        <box spacing={10} halign={Gtk.Align.CENTER}>
          <button
            class="profile-picture"
            tooltipMarkup={"Click to set up profile picture"}
            onClicked={async (self) => {
              try {
                const filename = await execAsync(
                  'zenity --file-selection --title="Select Profile Picture" --file-filter="Images (png, jpg, webp) | *.png *.jpg *.jpeg *.webp"',
                );

                if (!filename || filename.trim() === "") return;

                const cleanPath = filename.trim();

                await execAsync(
                  `cp -- ${JSON.stringify(cleanPath)} ${JSON.stringify(`${GLib.get_home_dir()}/.face.icon`)}`,
                );

                notify({
                  summary: "Success",
                  body: "User picture updated!",
                });

                const picture = (self.child as any).getPicture() as Gtk.Picture;
                picture.set_file(Gio.File.new_for_path(cleanPath));
              } catch (err) {
                const errorStr = String(err);
                if (errorStr.includes("exit status 1")) return;

                notify({
                  summary: "Error",
                  body: errorStr,
                });
              }
            }}
          >
            <Picture
              file={pfpPath}
              width={130}
              height={130}
            />
          </button>
        </box>
        
        <box class="user-details" orientation={Gtk.Orientation.VERTICAL} spacing={4}>
          <button 
            class="username-edit-btn" 
            onClicked={changeDisplayName}
            tooltipText="Click to edit Display Name"
            halign={Gtk.Align.CENTER}
          >
            <box spacing={8} halign={Gtk.Align.CENTER} class="user-name">
              <label label="I'm " />
              <label class="secondary font-bold" label={displayName} />
              <label class="edit-icon" label="󰏫" />
            </box>
          </button>
          
          <box class="desktop-env" halign={Gtk.Align.CENTER}>
            <label label="Running " />
            <label class="secondary" label={desktopEnv} />
          </box>
        </box>
      </box>
    );
  };

  const FastFetchDetails = () => {
    const StatRow = ({ icon, name, value }: { icon: string; name: string; value: any }) => (
      <box class="fetch-stat-row" spacing={10}>
        <label class="fetch-icon" label={icon} />
        <label class="fetch-label" label={name} />
        <label class="fetch-value secondary" label={value} hexpand halign={Gtk.Align.END} wrap />
      </box>
    );

    return (
      <box class="fastfetch-container" hexpand orientation={Gtk.Orientation.VERTICAL} spacing={8}>
        <box class="fetch-header" spacing={8}>
          <label class="fetch-header-icon" label="󰍹" />
          <label class="fetch-header-title font-bold" label="System Fetch" />
        </box>
        
        <box class="fetch-body" orientation={Gtk.Orientation.VERTICAL} spacing={6}>
          <StatRow icon="󰒋" name="OS" value={sysStats((s: any) => s.os)} />
          <StatRow icon="󰅐" name="OS Age" value={osAge} />
          <StatRow icon="󱄫" name="Uptime" value={uptime} />
          <StatRow icon="󰏖" name="Packages" value={sysStats((s: any) => String(s.packages))} />
          <StatRow icon="󰞀" name="Shell" value={sysStats((s: any) => s.shell)} />
          <StatRow icon="󰍛" name="Memory" value={sysStats((s: any) => s.memory)} />
          <StatRow icon="󰻠" name="CPU" value={sysStats((s: any) => s.cpu)} />
          <StatRow icon="󰢮" name="GPU" value={sysStats((s: any) => s.gpu)} />
        </box>
      </box>
    );
  };

  const hideAllPanels = () => {
    try {
      execAsync("ags -t left-panel").catch(() => {});
    } catch (_) {}
  };

  const SystemActions = () => {
    return (
      <box class="system-actions-grid" hexpand>
        <box homogeneous={true} hexpand>
          <button
            class="sys-btn logout"
            halign={Gtk.Align.CENTER}
            onClicked={() => {
              hyprland.dispatch("hl.dsp.exit()", "");
            }}
            tooltipText="Logout from Hyprland"
          >
            <label label="󰍃" />
          </button>

          <button
            class="sys-btn reboot"
            halign={Gtk.Align.CENTER}
            onClicked={() => {
              execAsync("reboot");
            }}
            tooltipText="Reboot Immediately"
          >
            <label label="󰜉" />
          </button>

          <button
            class="sys-btn sleep"
            halign={Gtk.Align.CENTER}
            onClicked={() => {
              hideAllPanels();
              execAsync(`bash -c "$HOME/.config/hypr/scripts/hyprlock.sh suspend"`);
            }}
            tooltipText="Put System to Sleep"
          >
            <label label="󰤄" />
          </button>

          <button
            class="sys-btn shutdown"
            halign={Gtk.Align.CENTER}
            onClicked={() => {
              execAsync("shutdown now");
            }}
            tooltipText="Shutdown Immediately"
          >
            <label label="" />
          </button>
        </box>
      </box>
    );
  };

  return (
    <scrolledwindow hexpand vexpand>
      <box
        class="profile-widget"
        orientation={Gtk.Orientation.VERTICAL}
        hexpand
        spacing={15}
      >
        {/* User Card */}
        {UserProfileCard()}

        {/* Quick System Actions */}
        {SystemActions()}

        {/* Fastfetch Stats */}
        {FastFetchDetails()}

        <box class="profile-separator" />

        {/* ArchZenith Info */}
        {GeneralInfo()}
      </box>
    </scrolledwindow>
  );
};
