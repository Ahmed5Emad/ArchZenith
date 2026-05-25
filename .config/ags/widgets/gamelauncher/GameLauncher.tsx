import { createState } from "ags";
import { execAsync } from "ags/process";
import GLib from "gi://GLib";
import { globalSettings } from "../../variables";

export interface GameEntry {
  id: string;
  name: string;
  runner: "steam" | "lutris" | "heroic";
  cover: string;
  run_command: string;
}

const [games, setGames] = createState<GameEntry[]>([]);
const [loading, setLoading] = createState(false);

const user = GLib.get_user_name();
const BINARY_PATH = `/tmp/ags-${user}/gamelauncher-ags`;

export { games, loading };

export async function refreshGames() {
  if (loading.peek()) return;
  setLoading(true);

  try {
    const settings: any = globalSettings.peek();
    const useSteam = settings.gameluancher?.steam?.value ?? false;
    const useHeroic = settings.gameluancher?.heroic?.value ?? false;

    const args = [BINARY_PATH];
    if (useSteam) args.push("--steam");
    if (useHeroic) args.push("--heroic");

    const out = await execAsync(args);
    const parsed: GameEntry[] = JSON.parse(out);
    setGames(parsed);
  } catch (e) {
    console.error("[GameLauncher] Error refreshing games:", e);
    setGames([]);
  } finally {
    setLoading(false);
  }
}
