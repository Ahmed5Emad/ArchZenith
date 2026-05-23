import { Gtk } from "ags/gtk4";
import GLib from "gi://GLib";
import { createPoll } from "ags/time";
import { Accessor } from "ags";

export default function ({
  className,
}: {
  className?: string | Accessor<string>;
}) {
  return (
    <box
      class={`calendar-widget ${className ?? ""}`}
      orientation={Gtk.Orientation.VERTICAL}
      spacing={8}
    >
      <box class="header" spacing={8}>
        <label
          class="title"
          label="Calendar"
          hexpand
          halign={Gtk.Align.START}
        />
      </box>
      <Gtk.Calendar
        canFocus={false}
        focusOnClick={false}
        cssClasses={["calendar"]}
      />
    </box>
  );
}
