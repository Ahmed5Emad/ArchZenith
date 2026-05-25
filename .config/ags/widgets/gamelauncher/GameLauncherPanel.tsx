import { Gtk } from "ags/gtk4";
import { createState, For } from "ags";
import Pango from "gi://Pango";
import GLib from "gi://GLib";
import Picture from "../Picture";

import { games, loading, refreshGames, GameEntry } from "./GameLauncher";

export default () => {
  const [GameList, setGameList] = createState<GameEntry[]>([]);

  refreshGames().then(() => {
    setGameList(games.get());
  }).catch(() => {});

  return (
    <scrolledwindow hexpand vexpand>
      <box
        class="game-launcher-panel"
        orientation={Gtk.Orientation.VERTICAL}
        hexpand
        spacing={5}
      >
        <box class="game-launcher-panel-header" spacing={5}>
          <label label="Game Launcher" hexpand xalign={0} />
          <button
            onClicked={() => refreshGames().then(() => setGameList(games.get())).catch(() => {})}
            tooltipText="Refresh games"
          >
            <label label="↻" />
          </button>
        </box>
        <For each={GameList}>
          {(game: GameEntry) => (
            <button
              class="game-launcher-panel-item"
              hexpand
              onClicked={() => {
                GLib.spawn_command_line_async(
                  `bash -c "${game.run_command}"`,
                );
              }}
            >
              <box spacing={8}>
                <box class="game-launcher-panel-cover">
                  <Picture file={game.cover} width={60} height={85}
                    contentFit={Gtk.ContentFit.COVER} visible={!!game.cover} />
                  <image hexpand vexpand iconName="applications-games" pixelSize={40}
                    visible={!game.cover} />
                </box>
                <box
                  orientation={Gtk.Orientation.VERTICAL}
                  spacing={2}
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
          visible={GameList((g: GameEntry[]) => g.length === 0)}
          marginTop={20}
        >
          <label
            label={loading((l: boolean) =>
              l ? "Searching for games..." : "No games found.",
            )}
            class="game-launcher-panel-empty"
          />
        </box>
      </box>
    </scrolledwindow>
  );
};
