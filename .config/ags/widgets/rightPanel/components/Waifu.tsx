import { Accessor, createState, With } from "ags";
import { globalSettings, setGlobalSetting } from "../../../variables";
import { Gtk } from "ags/gtk4";
import { WallpaperImage } from "../../../class/WallpaperImage";
import app from "ags/gtk4/app";
import { showWindow } from "../../../utils/window";
import { leftPanelWidgetSelectors } from "../../../constants/widget.constants";

function WaifuDisplay() {
  return (
    <With value={globalSettings(({ waifuWidget }) => waifuWidget.current)}>
      {(waifuData: any) => {
        const image = new WallpaperImage(waifuData || {});
        return image.renderAsWaifuWidget({
          width: globalSettings.peek().rightPanel.width,
        });
      }}
    </With>
  );
}

export default ({ className }: { className?: string | Accessor<string> }) => {
  return (
    <box
      class={`waifu ${className ?? ""}`}
      orientation={Gtk.Orientation.VERTICAL}
      css={"border-radius: 10px;"}
    >
      <WaifuDisplay />
    </box>
  );
};
