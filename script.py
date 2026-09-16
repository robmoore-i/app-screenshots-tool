import argparse
import shutil
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

# ── Devices ───────────────────────────────────────────────────────────────────

IPHONE = {
    "canvas_w":      1284,
    "canvas_h":      2778,
    "font_size":     89,
    "line_spacing":  19,
    "bezel":         26,
    "screen_radius": 90,
}

IPAD = {
    "canvas_w":      2064,
    "canvas_h":      2752,
    "font_size":     112,
    "line_spacing":  25,
    "bezel":         21,
    "screen_radius": 75,
}

# ── Frame defaults ─────────────────────────────────────────────────────────────

IPHONE_SCREEN_W         = 940
IPHONE_BOTTOM_MARGIN    = 120
IPHONE_TOP_PADDING      = 40
FRAME_COLOUR            = "#000000"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _rounded_mask(w, h, radius, supersample=4):
    """Return an 'L' mask with anti-aliased rounded corners via supersampling."""
    sw, sh, sr = w * supersample, h * supersample, radius * supersample
    big = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(big).rounded_rectangle([0, 0, sw - 1, sh - 1], radius=sr, fill=255)
    return big.resize((w, h), Image.LANCZOS)


def frame_screenshot(raw_path, screen_w, bezel, radius, frame_colour):
    """Wrap a raw screenshot in a simple iPhone-style bezel. Returns RGBA."""
    src = Image.open(raw_path).convert("RGBA")
    src_w, src_h = src.size
    screen_h = round(screen_w * src_h / src_w)

    screen = src.resize((screen_w, screen_h), Image.LANCZOS)
    screen.putalpha(_rounded_mask(screen_w, screen_h, radius))

    outer_w = screen_w + 2 * bezel
    outer_h = screen_h + 2 * bezel

    phone = Image.new("RGBA", (outer_w, outer_h), (0, 0, 0, 0))
    colour_layer = Image.new("RGBA", (outer_w, outer_h), frame_colour)
    phone.paste(colour_layer, mask=_rounded_mask(outer_w, outer_h, radius + bezel))
    phone.paste(screen, (bezel, bezel), mask=screen)

    return phone


def frame_geometry(device):
    scale = device["canvas_w"] / IPHONE["canvas_w"]
    return {
        "screen_w":      round(IPHONE_SCREEN_W * scale),
        "radius":        device["screen_radius"],
        "bottom_margin": round(IPHONE_BOTTOM_MARGIN * scale),
        "top_padding":   round(IPHONE_TOP_PADDING * scale),
        "frame_colour":  FRAME_COLOUR,
    }


# ── Rendering ─────────────────────────────────────────────────────────────────

def render(cfg):
    canvas_w, canvas_h = cfg["canvas_w"], cfg["canvas_h"]
    canvas = Image.new("RGBA", (canvas_w, canvas_h), cfg["bg"])

    phone = frame_screenshot(
        cfg["input"],
        cfg["screen_w"],
        cfg["bezel"],
        cfg["radius"],
        cfg["frame_colour"],
    )
    phone_w, phone_h = phone.size
    phone_x = (canvas_w - phone_w) // 2
    phone_y = canvas_h - cfg["bottom_margin"] - phone_h
    canvas.paste(phone, (phone_x, phone_y), mask=phone)

    lines = cfg["lines"]
    if lines and cfg.get("font"):
        line_spacing = cfg["line_spacing"]

        font = ImageFont.truetype(cfg["font"], size=cfg["font_size"])
        if cfg.get("font_axes"):
            font.set_variation_by_axes(cfg["font_axes"])

        draw     = ImageDraw.Draw(canvas)
        ref_bbox = draw.textbbox((0, 0), "Ag", font=font)
        line_h   = ref_bbox[3] - ref_bbox[1]
        total_h  = line_h * len(lines) + line_spacing * (len(lines) - 1)

        band_h = phone_y - cfg["top_padding"]
        y      = cfg["top_padding"] + max(0, (band_h - total_h) // 2)

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x    = (canvas_w - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, font=font, fill=cfg["text_colour"])
            y += line_h + line_spacing

    canvas.convert("RGB").save(cfg["output"], format="PNG")
    print(f"Saved {cfg['output']} — {canvas.size}")


def screenshot_styling(entry, bg, text_col, font_path, font_axes):
    return {
        "bg":          bg,
        "lines":       [l.strip() for l in str(entry.get("text", "")).split("|") if l.strip()],
        "text_colour": text_col,
        "font":        font_path,
        "font_axes":   font_axes,
    }


def render_for_device(input_file, output_file, styling, device):
    render({
        **styling,
        **device,
        **frame_geometry(device),
        "input":  str(input_file),
        "output": str(output_file),
    })


# ── Config-mode helpers ───────────────────────────────────────────────────────

def _normalise_hex(value, field):
    """Return '#RRGGBB'; exit with a clear error if the value isn't a valid 6-digit hex."""
    s = str(value).strip().lstrip("#")
    if len(s) != 6 or not all(c in "0123456789abcdefABCDEF" for c in s):
        sys.exit(f"Error: {field} value '{value}' is not a valid 6-digit hex colour.")
    return f"#{s.upper()}"


def _resolve_colours(raw_colours, entries):
    """Return one (background, text) hex pair per screenshot.

    Colours come from the top-level 'colours' list, which is positional: it stays
    put while the screenshots and their text are reordered. Configs written before
    that key existed carry the colours on each screenshot entry instead.
    """
    inline = [i for i, e in enumerate(entries)
              if "backgroundColour" in e or "textColour" in e]

    if raw_colours is None:
        pairs = []
        for i, entry in enumerate(entries):
            label = f"screenshots[{i}]"
            for key in ("backgroundColour", "textColour"):
                if key not in entry:
                    sys.exit(
                        f"Error: {label} is missing required key '{key}'.\n"
                        f"  Alternatively, set a top-level 'colours' list — one entry per "
                        f"screenshot — to keep the colour sequence fixed while reordering."
                    )
            pairs.append((
                _normalise_hex(entry["backgroundColour"], f"{label}.backgroundColour"),
                _normalise_hex(entry["textColour"],       f"{label}.textColour"),
            ))
        return pairs

    if inline:
        listed = ", ".join(str(i) for i in inline)
        sys.exit(
            f"Error: colours are set both in the top-level 'colours' list and on "
            f"screenshots entries {listed}.\n"
            f"  Remove 'backgroundColour' / 'textColour' from those screenshots entries."
        )

    if not isinstance(raw_colours, list):
        sys.exit("Error: 'colours' must be a list.")
    if len(raw_colours) != len(entries):
        sys.exit(
            f"Error: 'colours' has {len(raw_colours)} entries but 'screenshots' has "
            f"{len(entries)} — the two lists must be the same length."
        )

    pairs = []
    for i, colour in enumerate(raw_colours):
        label = f"colours[{i}]"
        if not isinstance(colour, dict):
            sys.exit(f"Error: {label} must be a mapping of 'backgroundColour' and 'textColour'.")
        for key in ("backgroundColour", "textColour"):
            if key not in colour:
                sys.exit(f"Error: {label} is missing required key '{key}'.")
        pairs.append((
            _normalise_hex(colour["backgroundColour"], f"{label}.backgroundColour"),
            _normalise_hex(colour["textColour"],       f"{label}.textColour"),
        ))
    return pairs


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def _images_in(directory):
    return sorted(p for p in directory.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)


def _find_input(input_dir, basename):
    """Return the single matching file for basename, or None; exit if more than one found."""
    found = [p for p in _images_in(input_dir) if p.stem == basename]
    if len(found) > 1:
        sys.exit(
            f"Error: ambiguous input for basename '{basename}' — multiple files found:\n"
            + "\n".join(f"  {p}" for p in found)
        )
    return found[0] if found else None


def _resolve_input(input_dir, basename):
    """Return the single matching file for basename; exit if zero or more than one found."""
    found = _find_input(input_dir, basename)
    if found is None:
        sys.exit(
            f"Error: no file found for basename '{basename}' in {input_dir}\n"
            f"  Looked for: {basename}.jpg / .jpeg / .png (any case)"
        )
    return found


def _reset_output_dir(output_dir, protected):
    """Delete and recreate output_dir so files from earlier runs don't linger.

    Refuses to delete a directory that holds any of the protected paths
    (config file, input directories, font), since that would destroy inputs.
    """
    for p in protected:
        if p is None:
            continue
        p = Path(p).resolve()
        if p == output_dir or output_dir in p.parents:
            sys.exit(
                f"Error: refusing to clear output directory {output_dir} because it contains {p}."
            )
    if output_dir.exists():
        if not output_dir.is_dir():
            sys.exit(f"Error: output path exists but is not a directory: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def run_from_config(config_path):
    config_path = Path(config_path).resolve()
    if not config_path.exists():
        sys.exit(f"Error: config file not found: {config_path}")

    with config_path.open() as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        sys.exit("Error: config file must be a YAML mapping.")

    config_dir = config_path.parent

    def _res(p):
        p = Path(p)
        return p if p.is_absolute() else (config_dir / p).resolve()

    for key in ("inputDirectory", "outputDirectory", "screenshots"):
        if key not in raw:
            sys.exit(f"Error: config is missing required key '{key}'.")

    input_dir  = _res(raw["inputDirectory"])
    output_dir = _res(raw["outputDirectory"])
    entries    = raw["screenshots"]

    if not isinstance(entries, list) or not entries:
        sys.exit("Error: 'screenshots' must be a non-empty list.")

    colours = _resolve_colours(raw.get("colours"), entries)

    font_cfg      = raw.get("font") or {}
    font_path     = str(_res(font_cfg["path"])) if font_cfg.get("path") else None
    font_axes_raw = font_cfg.get("axes")
    font_axes     = [float(v) for v in str(font_axes_raw).split(",")] if font_axes_raw else None

    if any(str(e.get("text", "")).strip() for e in entries) and not font_path:
        sys.exit("Error: 'font.path' is required when any screenshot has text.")

    ipad_in_raw  = raw.get("ipadInputDirectory")
    ipad_out_raw = raw.get("ipadOutputDirectory")
    if bool(ipad_in_raw) != bool(ipad_out_raw):
        missing = "ipadOutputDirectory" if ipad_in_raw else "ipadInputDirectory"
        sys.exit(f"Error: '{missing}' must be set when the other iPad directory key is set.")
    ipad_in  = _res(ipad_in_raw)  if ipad_in_raw  else None
    ipad_out = _res(ipad_out_raw) if ipad_out_raw else None

    # Clear old output first so each run produces exactly the configured files.
    protected = [config_path, input_dir, ipad_in, font_path]
    _reset_output_dir(output_dir, protected)

    for i, (entry, (bg, text_col)) in enumerate(zip(entries, colours)):
        if "inputBasename" not in entry:
            sys.exit(f"Error: screenshots[{i}] is missing required key 'inputBasename'.")

        basename = entry["inputBasename"]
        render_for_device(
            _resolve_input(input_dir, basename),
            output_dir / f"screenshot-{i + 1}-{basename}_processed.png",
            screenshot_styling(entry, bg, text_col, font_path, font_axes),
            IPHONE,
        )

    if ipad_in and ipad_out:
        if not ipad_in.is_dir():
            sys.exit(f"Error: ipadInputDirectory not found: {ipad_in}")
        ipad_images = _images_in(ipad_in)
        if not ipad_images:
            sys.exit(f"Error: no images found in ipadInputDirectory: {ipad_in}")
        _reset_output_dir(ipad_out, protected)

        rendered = []
        for entry, (bg, text_col) in zip(entries, colours):
            basename  = entry["inputBasename"]
            ipad_file = _find_input(ipad_in, basename)
            if ipad_file is None:
                continue
            rendered.append(ipad_file)
            render_for_device(
                ipad_file,
                ipad_out / f"screenshot-{len(rendered)}-{basename}_processed.png",
                screenshot_styling(entry, bg, text_col, font_path, font_axes),
                IPAD,
            )

        skipped = [p.name for p in ipad_images if p not in rendered]
        if skipped:
            print(f"Skipped, no screenshots entry matches: {', '.join(skipped)}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Produce App Store screenshots: 1284×2778 for iPhone, 2064×2752 for iPad."
    )
    parser.add_argument("input", nargs="?",
                        help="Path to the raw screenshot (JPEG/PNG). Omit to run from config.yaml.")
    parser.add_argument("--config", default=None, metavar="PATH",
                        help="YAML config file for batch mode (default: ./config.yaml).")
    parser.add_argument("-o", "--output", default=None,
                        help="Output PNG path. Default: <input_stem>_final.png beside input.")
    parser.add_argument("--bg", default="#FFFFFF",
                        help="Background colour hex (default: '#FFFFFF').")
    parser.add_argument("--text", default="",
                        help="Text lines separated by '|', e.g. 'Line one|Line two'.")
    parser.add_argument("--text-colour", default="#000000",
                        help="Text colour hex (default: '#000000').")
    parser.add_argument("--font", default=None,
                        help="Path to a .ttf font file. Required when --text is provided.")
    parser.add_argument("--font-axes", default=None,
                        help="Comma-separated variation axes, e.g. '600,100'. Optional.")
    # Frame tuning
    parser.add_argument("--screen-width",   type=int, default=IPHONE_SCREEN_W,
                        help=f"Screenshot width inside bezel in px (default: {IPHONE_SCREEN_W}).")
    parser.add_argument("--bezel",          type=int, default=IPHONE["bezel"],
                        help=f"Bezel border thickness in px (default: {IPHONE['bezel']}).")
    parser.add_argument("--radius",         type=int, default=IPHONE["screen_radius"],
                        help=f"Inner corner radius in px (default: {IPHONE['screen_radius']}).")
    parser.add_argument("--bottom-margin",  type=int, default=IPHONE_BOTTOM_MARGIN,
                        help=f"Gap below phone in px (default: {IPHONE_BOTTOM_MARGIN}).")
    parser.add_argument("--top-padding",    type=int, default=IPHONE_TOP_PADDING,
                        help=f"Minimum gap above text in px (default: {IPHONE_TOP_PADDING}).")
    parser.add_argument("--frame-colour",   default=FRAME_COLOUR,
                        help=f"Bezel colour hex (default: '{FRAME_COLOUR}').")

    args = parser.parse_args()

    # Config mode: no positional input, or --config given explicitly.
    if args.input is None or args.config is not None:
        run_from_config(args.config or "config.yaml")
        sys.exit(0)

    # Single-image mode (original behaviour).
    if args.output is None:
        p = Path(args.input)
        args.output = str(p.parent / (p.stem + "_final.png"))

    lines = [l.strip() for l in args.text.split("|") if l.strip()]

    if lines and not args.font:
        parser.error("--font is required when --text is provided.")

    font_axes = [float(v) for v in args.font_axes.split(",")] if args.font_axes else None

    render({
        **IPHONE,
        "input":         args.input,
        "output":        args.output,
        "bg":            args.bg,
        "lines":         lines,
        "text_colour":   args.text_colour,
        "font":          args.font,
        "font_axes":     font_axes,
        "screen_w":      args.screen_width,
        "bezel":         args.bezel,
        "radius":        args.radius,
        "bottom_margin": args.bottom_margin,
        "top_padding":   args.top_padding,
        "frame_colour":  args.frame_colour,
    })
