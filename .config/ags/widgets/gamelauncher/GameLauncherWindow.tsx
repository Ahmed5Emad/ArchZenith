import { createState, createComputed, For } from "ags";
import app from "ags/gtk4/app";
import { Astal, Gtk, Gdk } from "ags/gtk4";
import Pango from "gi://Pango";
import GLib from "gi://GLib";

import { getMonitorName } from "../../utils/monitor";
import { games, loading, refreshGames, GameEntry } from "./GameLauncher";

export default ({
  monitor,
  setup,
}: {
  monitor: Gdk.Monitor;
  setup: (self: Gtk.Window) => void;
}) => {
  const [filtered, setFiltered] = createState<GameEntry[]>([]);
  const [searchText, setSearchText] = createState("");
  const [selectedIndex, setSelectedIndex] = createState(0);
  let parentWindowRef: Gtk.Window | null = null;
  let entryWidget: Gtk.TextView | null = null;
  let listContainer: Gtk.Box | null = null;
  let scrollWin: Gtk.ScrolledWindow | null = null;
  let panelContainer: Gtk.Box | null = null;

  function scrollToSelected() {
    const idx = selectedIndex.get();
    const sw = scrollWin;
    if (!sw) return;
    const adj = sw.get_vadjustment();
    if (!adj) return;
    const itemTop = idx * 105;
    const viewTop = adj.get_value();
    const viewBottom = viewTop + adj.get_page_size();
    if (itemTop < viewTop || itemTop + 105 > viewBottom) {
      GLib.idle_add(GLib.PRIORITY_HIGH_IDLE, () => {
        adj.set_value(Math.max(0, itemTop - adj.get_page_size() / 3));
        return GLib.SOURCE_REMOVE;
      });
    }
  }

  function filterGames(text: string) {
    const all = games.get();
    if (!text.trim()) { setFiltered(all); return; }
    const lower = text.toLowerCase();
    setFiltered(all.filter((g) => g.name.toLowerCase().includes(lower)));
  }

  function launchGame(game: GameEntry) {
    GLib.spawn_command_line_async(`bash -c "${game.run_command}"`);
    if (parentWindowRef) parentWindowRef.hide();
    setSearchText("");
    setSelectedIndex(0);
    setFiltered([]);
  }

  const monitorName = getMonitorName(monitor);

  return (
    <window
      gdkmonitor={monitor}
      name={`game-launcher-${monitorName}`}
      namespace="game-launcher"
      application={app}
      keymode={Astal.Keymode.EXCLUSIVE}
      layer={Astal.Layer.TOP}
      marginTop={5}
      marginBottom={5}
      marginLeft={5}
      visible={false}
      anchor={Astal.WindowAnchor.LEFT | Astal.WindowAnchor.TOP | Astal.WindowAnchor.BOTTOM}
      exclusivity={Astal.Exclusivity.EXCLUSIVE}
      class="game-launcher-panel"
      $={(self) => {
        parentWindowRef = self;
        setup(self);
        self.connect("notify::visible", () => {
          if (self.visible) {
            refreshGames().then(() => {
              filterGames(searchText.get());
            }).catch(() => {});
            if (entryWidget) {
              entryWidget.buffer.text = "";
              entryWidget.grab_focus();
            }
          }
        });
      }}
    >
      <Gtk.GestureClick
        onPressed={(_, _nPress, x: number, y: number) => {
          if (!parentWindowRef || !panelContainer) return;
          const picked = parentWindowRef.pick(x, y, Gtk.PickFlags.DEFAULT);
          let current = picked;
          while (current) {
            if (current === panelContainer) {
              return;
            }
            current = current.get_parent();
          }
          parentWindowRef.hide();
          setSearchText("");
          setSelectedIndex(0);
          setFiltered([]);
        }}
      />

      <Gtk.EventControllerKey
        onKeyPressed={({ widget }, keyval: number) => {
          if (keyval === Gdk.KEY_Escape) {
            parentWindowRef?.hide();
            return true;
          }
        }}
      />

      <box
        class="game-launcher-panel-content"
        orientation={Gtk.Orientation.VERTICAL}
        spacing={0}
        widthRequest={500}
        $={(self) => { panelContainer = self; }}
      >
        <box class="game-launcher-panel-header" spacing={10}>
          <image iconName="applications-games" />
          <label label="Game Launcher" hexpand xalign={0} />
          <label
            label={loading((l) => (l ? "Scanning..." : ""))}
            class="game-launcher-panel-status"
          />
          <button
            onClicked={() => refreshGames().then(() => filterGames(searchText.get())).catch(() => {})}
            tooltipText="Refresh games"
          >
            <label label="↻" />
          </button>
        </box>

        <box class="game-launcher-panel-search">
          <Gtk.TextView
            hexpand
            wrapMode={Gtk.WrapMode.WORD_CHAR}
            topMargin={8}
            bottomMargin={8}
            leftMargin={10}
            rightMargin={10}
            tooltipMarkup={"Search games\n<b>Enter</b> launch selected\n<b>Shift+Enter</b> new line"}
            $={(self) => {
              entryWidget = self;
              self.buffer.connect("changed", () => {
                const text = self.buffer.text;
                setSearchText(text);
                filterGames(text);
                setSelectedIndex(0);
              });
            }}
          >
            <Gtk.EventControllerKey
              onKeyPressed={(_, keyval: number, _keycode: number, state: number) => {
                const count = filtered.get().length;
                if (keyval === Gdk.KEY_Down && count > 0) {
                  setSelectedIndex((selectedIndex.get() + 1) % count);
                  scrollToSelected();
                  return true;
                }
                if (keyval === Gdk.KEY_Up && count > 0) {
                  setSelectedIndex((selectedIndex.get() - 1 + count) % count);
                  scrollToSelected();
                  return true;
                }
                const isEnter = keyval === Gdk.KEY_Return || keyval === Gdk.KEY_KP_Enter;
                if (!isEnter) return false;
                const isShift = (state & Gdk.ModifierType.SHIFT_MASK) !== 0;
                if (isShift) return false;
                if (count > 0) {
                  const idx = selectedIndex.get();
                  if (idx >= 0 && idx < count) launchGame(filtered.get()[idx]);
                }
                return true;
              }}
            />
          </Gtk.TextView>
        </box>

        <scrolledwindow vexpand $={(self) => { scrollWin = self; }}>
          <box
            orientation={Gtk.Orientation.VERTICAL}
            spacing={5}
            marginTop={5}
            marginBottom={10}
            marginStart={10}
            marginEnd={10}
            $={(self) => { listContainer = self; }}
          >
            <For each={filtered}>
              {(game: GameEntry, index: number) => (
                <button
                  hexpand
                  class={createComputed(() =>
                    selectedIndex() === index()
                      ? "game-launcher-panel-item checked"
                      : "game-launcher-panel-item"
                  )}
                  onClicked={() => launchGame(game)}
                >
                  <box spacing={10}>
                    <box
                      class="game-launcher-panel-cover"
                      css={
                        game.cover
                          ? `background-image: url('file://${game.cover}'); background-size: cover; background-position: center;`
                          : ""
                      }
                      widthRequest={60}
                      heightRequest={85}
                    >
                      {!game.cover && (
                        <image hexpand vexpand iconName="applications-games" pixelSize={40} />
                      )}
                    </box>
                    <box
                      orientation={Gtk.Orientation.VERTICAL}
                      spacing={3}
                      valign={Gtk.Align.CENTER}
                      hexpand
                    >
                      <label
                        label={game.name}
                        ellipsize={Pango.EllipsizeMode.END}
                        hexpand
                        xalign={0}
                        wrap={false}
                      />
                      <label
                        label={game.runner}
                        class="game-launcher-panel-runner"
                        xalign={0}
                        hexpand
                      />
                    </box>
                  </box>
                </button>
              )}
            </For>
            <box
              valign={Gtk.Align.CENTER}
              halign={Gtk.Align.CENTER}
              visible={filtered((f: GameEntry[]) => f.length === 0)}
              marginTop={40}
            >
              <label
                label={loading((l) => (l ? "Searching for games..." : "No games found."))}
                class="game-launcher-panel-empty"
              />
            </box>
          </box>
        </scrolledwindow>
      </box>
    </window>
  );
};
