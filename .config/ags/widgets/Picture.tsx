import { Accessor, createState, createBinding } from "ags";
import Gdk from "gi://Gdk";
import Gio from "gi://Gio";
import { Gtk } from "ags/gtk4";
import GLib from "gi://GLib";
import { execAsync } from "ags/process";

interface PictureProps {
  class?: Accessor<string> | string;
  height?: Accessor<number> | number;
  width?: Accessor<number> | number;
  file?: Accessor<string> | string;
  paintable?: Accessor<Gdk.Texture> | Gdk.Texture;
  contentFit?: Gtk.ContentFit;
  info?: string[];
  $?: (self: Gtk.Picture) => void;
}

export default function Picture({
  class: className,
  height,
  width,
  file,
  contentFit = Gtk.ContentFit.COVER,
  paintable,
  info,
  $,
}: PictureProps) {
  const [resolvedPath, setResolvedPath] = createState<string>("");

  const processPath = (path: string) => {
    if (!path || typeof path !== "string") {
      setResolvedPath("");
      return;
    }

    if (path.startsWith("file://")) {
      setResolvedPath(path.replace("file://", ""));
      return;
    }

    if (path.startsWith("http://") || path.startsWith("https://")) {
      try {
        const hash = GLib.compute_checksum_for_string(GLib.ChecksumType.MD5, path, -1);
        const cacheDir = `${GLib.get_user_cache_dir()}/ags/media`;

        GLib.mkdir_with_parents(cacheDir, 0o755);
        const localPath = `${cacheDir}/${hash}`;

        if (GLib.file_test(localPath, GLib.FileTest.EXISTS)) {
          setResolvedPath(localPath);
        } else {
          execAsync(["curl", "-s", "-f", "-L", "-A", "Mozilla/5.0", "-o", localPath, path])
            .then(() => {
              setResolvedPath(localPath);
            })
            .catch((err) => {
              console.error("Failed to download cover art:", err);
              setResolvedPath("");
            });
        }
      } catch (e) {
        console.error("Error hashing or checking local path:", e);
        setResolvedPath("");
      }
      return;
    }

    setResolvedPath(path);
  };

  if (file != undefined) {
    if (typeof file === "string") {
      processPath(file);
    } else if (file.subscribe) {
      file.subscribe((val) => processPath(val));
      const initial = file.get ? file.get() : "";
      if (initial) processPath(initial);
    }
  }

  return (
    <overlay
      class="image"
      heightRequest={height}
      widthRequest={width}
      $={(self) => {
        // Expose a lookup helper without holding a long-lived strong reference.
        (self as any).getPicture = () => {
          const children = self.observe_children();
          const count = children.get_n_items();

          for (let i = 0; i < count; i++) {
            const child = children.get_item(i);

            if (child instanceof Gtk.Picture) {
              return child;
            }
          }

          return undefined;
        };
      }}
    >
      <Gtk.Picture
        $type="overlay"
        class={
          className != undefined
            ? typeof className === "string"
              ? "image " + className
              : className!((c) => "image " + c)
            : "image"
        }
        file={resolvedPath((p) =>
          p ? Gio.File.new_for_path(p) : null
        )}
        paintable={
          paintable != undefined
            ? typeof paintable === "object"
              ? paintable
              : paintable!((p) => p)
            : undefined
        }
        contentFit={contentFit}
        $={(self) => {
          if ($) {
            $.call(undefined, self);
          }
        }}
      />

      <box
        $type="overlay"
        class="image-info"
        halign={Gtk.Align.END}
        valign={Gtk.Align.END}
        visible={info != undefined}
        spacing={5}
      >
        {info?.map((i) => (
          <label class={"image-info-item"} label={i} />
        ))}
      </box>
    </overlay>
  );
}

