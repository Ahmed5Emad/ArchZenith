import { createState, createComputed, For } from "ags";
import app from "ags/gtk4/app";
import { Astal, Gtk, Gdk } from "ags/gtk4";
import Pango from "gi://Pango";
import GLib from "gi://GLib";
import Picture from "../Picture";

import { globalMargin } from "../../variables";
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

  function scrollToSelected() {
    const idx = selectedIndex.get();
    const container = listContainer;
    if (!container) return;
    let sw = container.get_parent();
    while (sw && !(sw instanceof Gtk.ScrolledWindow)) {
      sw = sw.get_parent();
    }
    if (!sw) return;
    const adj = sw.get_vadjustment();
    if (!adj) return;
    const itemTop = idx * 80;
    const itemBottom = itemTop + 80;
    const viewTop = adj.get_value();
    const viewBottom = viewTop + adj.get_page_size();
    if (itemBottom > viewBottom || itemTop < viewTop) {
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
  }

  return (
    <Astal.Window
      gdkmonitor={monitor}
      name={`game-launcher-${getMonitorName(monitor)}`}
      namespace="game-launcher"
      application={app}
      keymode={Astal.Keymode.EXCLUSIVE}
      layer={Astal.Layer.TOP}
      margin={globalMargin}
      visible={false}
      anchor={Astal.WindowAnchor.TOP}
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
      resizable={false}
    >
      <Gtk.EventControllerKey
        onKeyPressed={({ widget }, keyval: number) => {
          if (keyval === Gdk.KEY_Escape) { widget.hide(); return true; }
        }}
      />
      <box class="game-launcher" orientation={Gtk.Orientation.VERTICAL} spacing={0} widthRequest={600}>
        <box class="game-launcher-header" spacing={10}>
          <image iconName="applications-games" />
          <label label="Game Launcher" hexpand xalign={0} />
          <label label={loading((l) => (l ? "Scanning..." : ""))} class="game-launcher-status" />
        </box>

        <Gtk.TextView hexpand
          wrapMode={Gtk.WrapMode.WORD_CHAR}
          topMargin={8} bottomMargin={8} leftMargin={10} rightMargin={10}
          $={(self) => {
            entryWidget = self;
            self.buffer.connect("changed", () => {
              const text = self.buffer.text; setSearchText(text); filterGames(text); setSelectedIndex(0);
            });
          }}>
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

        <scrolledwindow vexpand $={(self) => { scrollWin = self; }}>
          <box orientation={Gtk.Orientation.VERTICAL} spacing={5} marginTop={5} marginBottom={10} marginStart={10} marginEnd={10}
            $={(self) => { listContainer = self; }}>
            <For each={filtered}>
              {(game: GameEntry, index: number) => (
                <Gtk.Button hexpand
                  class={createComputed(() => selectedIndex() === index() ? "game-launcher-item checked" : "game-launcher-item")}
                  onClicked={() => launchGame(game)}>
                  <box spacing={10}>
                    <box class="game-launcher-cover">
                      <Picture file={game.cover} width={60} height={85}
                        contentFit={Gtk.ContentFit.COVER} visible={!!game.cover} />
                      <image hexpand vexpand iconName="applications-games" pixelSize={40}
                        visible={!game.cover} />
                    </box>
                    <box orientation={Gtk.Orientation.VERTICAL} spacing={3}
                      valign={Gtk.Align.CENTER} hexpand>
                      <label label={game.name} ellipsize={Pango.EllipsizeMode.END}
                        hexpand xalign={0} wrap={false} />
                      <label label={game.runner} class="game-launcher-runner" xalign={0} hexpand />
                    </box>
                  </box>
                </Gtk.Button>
              )}
            </For>
            <box valign={Gtk.Align.CENTER} halign={Gtk.Align.CENTER}
              visible={filtered((f: GameEntry[]) => f.length === 0)} marginTop={40}>
              <label label={loading((l) => l ? "Searching for games..." : "No games found.")}
                class="game-launcher-empty" />
            </box>
          </box>
        </scrolledwindow>
      </box>
    </Astal.Window>
  );
};
