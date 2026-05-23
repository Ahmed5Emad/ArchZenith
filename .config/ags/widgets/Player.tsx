import AstalMpris from "gi://AstalMpris";
import { Gtk } from "ags/gtk4";
import { createBinding, createState, Accessor } from "ags";
import GLib from "gi://GLib";
import Pango from "gi://Pango";
import AstalApps from "gi://AstalApps";
import Cava from "./Cava";
import Gio from "gi://Gio";
import { execAsync } from "ags/process";

const CACHE_DIR = `${GLib.get_user_cache_dir()}/ags/media`;
const DEFAULT_COVER = `${GLib.get_home_dir()}/.config/ags/assets/player/player_default.png`;

/**
 * Try to extract a YouTube thumbnail URL from the player's MPRIS metadata.
 * Firefox/Zen doesn't set mpris:artUrl for YouTube, but may set xesam:url
 * to the YouTube page URL, from which we can extract the video ID.
 */
export function getYoutubeThumbUrl(player: AstalMpris.Player): string | null {
  const metaVar = (player as any).metadata;
  if (!metaVar) return null;
  // metadata is a GLib.Variant — need recursiveUnpack() to get plain JS values
  let meta: Record<string, unknown> | null = null;
  try {
    meta = typeof metaVar.recursiveUnpack === "function"
      ? metaVar.recursiveUnpack()
      : metaVar;
  } catch {}
  if (!meta || typeof meta !== "object") return null;
  const pageUrl = meta["xesam:url"];
  if (!pageUrl || typeof pageUrl !== "string") return null;
  // Match youtube.com, music.youtube.com, youtu.be
  const match = pageUrl.match(
    /(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?([a-zA-Z0-9_-]{11})/,
  );
  if (match) {
    return `https://i.ytimg.com/vi/${match[1]}/maxresdefault.jpg`;
  }
  return null;
}

export function downloadCover(url: string): Promise<string | null> {
  try {
    if (url.startsWith("file://")) {
      const localPath = decodeURIComponent(url.replace("file://", ""));
      if (GLib.file_test(localPath, GLib.FileTest.EXISTS)) {
        return Promise.resolve(localPath);
      }
      return Promise.resolve(null);
    }

    GLib.mkdir_with_parents(CACHE_DIR, 0o755);
    const hash = GLib.compute_checksum_for_string(GLib.ChecksumType.MD5, url, -1);
    const localPath = `${CACHE_DIR}/${hash}`;
    if (GLib.file_test(localPath, GLib.FileTest.EXISTS)) {
      return Promise.resolve(localPath);
    }
    return execAsync(["curl", "-s", "-f", "-L", "-A", "Mozilla/5.0", "-e", "https://www.youtube.com", "-o", localPath, url])
      .then(() => localPath)
      .catch(() => null);
  } catch {
    return Promise.resolve(null);
  }
}

export default ({
  player,
  width,
  height,
  className,
}: {
  player: AstalMpris.Player;
  width?: Accessor<number> | number;
  height?: Accessor<number> | number;
  className?: string;
}) => {
  const apps = new AstalApps.Apps();

  const [isDragging, setIsDragging] = createState(false);
  const [parentWidth, setParentWidth] = createState(0);
  const [slideDirection, setSlideDirection] = createState<"next" | "prev">(
    "next",
  );
  const [coverPath, setCoverPath] = createState<string>(DEFAULT_COVER);

  const isPlaying = createBinding(
    player,
    "playbackStatus",
  )((status) => status === AstalMpris.PlaybackStatus.PLAYING);

  function lengthStr(length: number) {
    const min = Math.floor(length / 60);
    const sec = Math.floor(length % 60);
    const sec0 = sec < 10 ? "0" : "";
    return `${min}:${sec0}${sec}`;
  }

  const bottomBar = () => {
    const title = (
      <label
        class="title"
        ellipsize={Pango.EllipsizeMode.END}
        halign={Gtk.Align.START}
        label={createBinding(player, "title")((t) => t || "Unknown Track")}
      />
    );

    const artist = (
      <label
        class="artist"
        maxWidthChars={20}
        halign={Gtk.Align.START}
        ellipsize={Pango.EllipsizeMode.END}
        label={createBinding(player, "artist")((a) => a || "Unknown Artist")}
      />
    );

    const positionSlider = (
      <slider
        class="slider"
        $={(self) => {
          let unsubscribe: (() => void) | null = null;
          const updateValue = () => {
            if (!isDragging.get()) {
              const pos = player.position;
              const len = player.length;
              self.set_value(len > 0 ? pos / len : 0);
            }
          };
          const gestureClick = new Gtk.GestureDrag();
          gestureClick.connect("drag-begin", () => {
            setIsDragging(true);
            unsubscribe?.();
            unsubscribe = null;
          });
          gestureClick.connect("drag-update", () => {
            player.position = self.get_value() * player.length;
          });
          gestureClick.connect("drag-end", () => {
            player.position = self.get_value() * player.length;
            setIsDragging(false);
            unsubscribe = createBinding(player, "position").subscribe(updateValue);
          });
          self.add_controller(gestureClick);
          unsubscribe = createBinding(player, "position").subscribe(updateValue);
        }}
        visible={createBinding(player, "length")((l) => l > 0)}
      />
    );

    const positionLabel = (
      <label
        class="position time"
        halign={Gtk.Align.START}
        label={createBinding(player, "position")(lengthStr)}
        visible={createBinding(player, "length")((l) => l > 0)}
      />
    );

    const lengthLabel = (
      <label
        class="length time"
        halign={Gtk.Align.END}
        visible={createBinding(player, "length")((l) => l > 0)}
        label={createBinding(player, "length")(lengthStr)}
      />
    );

    const Icon = () => (
      <box hexpand halign={Gtk.Align.END} valign={Gtk.Align.START}>
        <image
          class="icon"
          tooltip_text={createBinding(player, "identity")((i) => i || "")}
          iconName={apps.exact_query(player.entry)[0]?.iconName || "audio-x-generic"}
        />
      </box>
    );

    const playPause = (
      <button
        onClicked={() => player.play_pause()}
        class="play-pause"
        visible={createBinding(player, "can_play")((c) => c)}
      >
        <label
          label={createBinding(player, "playbackStatus")((s) => {
            switch (s) {
              case AstalMpris.PlaybackStatus.PLAYING: return "";
              case AstalMpris.PlaybackStatus.PAUSED:
              case AstalMpris.PlaybackStatus.STOPPED: return "";
              default: return "";
            }
          })}
        />
      </button>
    );

    const prev = (
      <button
        onClicked={() => { player.previous(); setSlideDirection("prev"); }}
        visible={createBinding(player, "can_go_previous")((c) => c)}
      >
        <label label="󰒮" />
      </button>
    );

    const next = (
      <button
        onClicked={() => { player.next(); setSlideDirection("next"); }}
        visible={createBinding(player, "can_go_next")((c) => c)}
      >
        <label label="󰒭" />
      </button>
    );

    return (
      <box class="bottom-bar" spacing={5} orientation={Gtk.Orientation.VERTICAL} hexpand>
        <box class="top-row" spacing={10}>
          <overlay heightRequest={40} widthRequest={40}>
            <image
              pixelSize={30}
              iconName="audio-x-generic-symbolic"
              visible={coverPath((p) => !p || p === DEFAULT_COVER)}
            />
            <Gtk.Picture
              $type="overlay"
              class={createBinding(player, "playbackStatus")((s) =>
                s === AstalMpris.PlaybackStatus.PLAYING
                  ? "cover-art-spinner playing"
                  : "cover-art-spinner paused"
              )}
              visible={coverPath((p) => !!p && p !== DEFAULT_COVER)}
              file={coverPath((p) =>
                p && p !== DEFAULT_COVER ? Gio.File.new_for_path(p) : null
              )}
              contentFit={Gtk.ContentFit.COVER}
            />
          </overlay>
          <box class="info" orientation={Gtk.Orientation.VERTICAL}>
            {title}
            {artist}
          </box>
          <Icon />
        </box>
        <box class="separator" vexpand />
        <centerbox>
          <box $type="start">{positionLabel}</box>
          <box $type="center" spacing={5}>
            {prev}
            {playPause}
            {next}
          </box>
          <box $type="end">{lengthLabel}</box>
        </centerbox>
        {positionSlider}
      </box>
    );
  };

  const playerStack = new Gtk.Stack({
    transition_duration: 250,
    hexpand: true,
    vexpand: true,
  });

  const bar1 = bottomBar() as Gtk.Widget;
  const bar2 = bottomBar() as Gtk.Widget;

  let currentIndex = 0;
  const names = ["bar1", "bar2"];

  playerStack.add_named(bar1, names[0]);
  playerStack.add_named(bar2, names[1]);
  playerStack.set_visible_child_name(names[0]);

  function switchBar(direction: "next" | "prev") {
    playerStack.set_transition_type(
      direction === "next"
        ? Gtk.StackTransitionType.SLIDE_LEFT
        : Gtk.StackTransitionType.SLIDE_RIGHT,
    );
    currentIndex = currentIndex === 0 ? 1 : 0;
    playerStack.set_visible_child_name(names[currentIndex]);
  }

  const overlay = (
    <overlay
      class={`player ${className || ""}`}
      hexpand
      $={(self) => {
        const controller = new Gtk.EventControllerMotion();
        controller.connect("enter", () => {
          const alloc = self.get_allocation();
          if (alloc) setParentWidth(alloc.width);
        });

        const checkWidth = () => {
          const alloc = self.get_allocation();
          if (alloc && alloc.width > 0 && alloc.width !== parentWidth.get()) {
            setParentWidth(alloc.width);
          }
          return true;
        };

        const timeoutId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 100, checkWidth);
        self.add_controller(controller);
        checkWidth();

        createBinding(player, "title").subscribe(() => {
          switchBar(slideDirection.get() || "next");
        });

        let lastUrl: string | null = null;
        let lastFailed = false;
        const tryCover = (url: string) => {
          downloadCover(url).then((p) => {
            if (p) { setCoverPath(p); lastFailed = false; lastUrl = url; }
            else { lastFailed = true; }
          });
        };
        const findCoverUrl = (): string | null => {
          return player.artUrl || getYoutubeThumbUrl(player) || null;
        };
        const initialUrl = findCoverUrl();
        if (initialUrl) tryCover(initialUrl);
        const coverTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 2000, () => {
          const url = findCoverUrl();
          if (url && (url !== lastUrl || lastFailed)) {
            tryCover(url);
          }
          return GLib.SOURCE_CONTINUE;
        });
        self.connect("destroy", () => {
          GLib.source_remove(timeoutId);
          GLib.source_remove(coverTimer);
        });
      }}
    >
      <overlay heightRequest={height} widthRequest={width}>
        <Gtk.Picture
          $type="overlay"
          class="img"
          visible={coverPath((p) => !!p && p !== DEFAULT_COVER)}
          file={coverPath((p) =>
            p && p !== DEFAULT_COVER ? Gio.File.new_for_path(p) : null
          )}
          contentFit={Gtk.ContentFit.COVER}
        />
      </overlay>

      <box
        $type="overlay"
        orientation={Gtk.Orientation.VERTICAL}
        valign={Gtk.Align.END}
      >
        <Cava
          transitionType={Gtk.RevealerTransitionType.SLIDE_UP}
          barCount={50}
        />
        {playerStack}
      </box>
    </overlay>
  );

  return overlay;
};
