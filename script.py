import argparse
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

# ── Canvas ────────────────────────────────────────────────────────────────────

CANVAS_W, CANVAS_H = 1284, 2778

IPAD_W, IPAD_H  = 2064, 2752
IPAD_PAD_COLOUR = "#FFFFFF"

# ── Text defaults ─────────────────────────────────────────────────────────────

# Base values were tuned at BASE_WIDTH px wide; scale to actual canvas width.
BASE_WIDTH        = 922
BASE_FONT_SIZE    = 64
BASE_LINE_SPACING = 14

# ── Frame defaults ─────────────────────────────────────────────────────────────

DEFAULT_SCREEN_W      = 940    # width of the scaled screenshot inside the bezel
DEFAULT_BEZEL         = 26     # bezel border thickness (px)
DEFAULT_RADIUS        = 90     # inner (screen) corner radius (px)
DEFAULT_BOTTOM_MARGIN = 120    # gap between phone bottom and canvas bottom
DEFAULT_TOP_PADDING   = 40     # minimum gap above text block
DEFAULT_FRAME_COLOUR  = "#000000"

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


def fit_and_pad(src_path, target_w, target_h, bg):
    """Scale preserving aspect to fit target, centre on a bg-filled canvas."""
    src = Image.open(src_path).convert("RGB")
    w, h = src.size
    scale = min(target_w / w, target_h / h)
    new_w, new_h = round(w * scale), round(h * scale)
    scaled = src.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGB", (target_w, target_h), bg)
    canvas.paste(scaled, ((target_w - new_w) // 2, (target_h - new_h) // 2))
    return canvas


# ── Rendering ─────────────────────────────────────────────────────────────────

def render(cfg):
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), cfg["bg"])

    phone = frame_screenshot(
        cfg["input"],
        cfg["screen_w"],
        cfg["bezel"],
        cfg["radius"],
        cfg["frame_colour"],
    )
    phone_w, phone_h = phone.size
    phone_x = (CANVAS_W - phone_w) // 2
    phone_y = CANVAS_H - cfg["bottom_margin"] - phone_h
    canvas.paste(phone, (phone_x, phone_y), mask=phone)

    lines = cfg["lines"]
    if lines and cfg.get("font"):
        scale        = CANVAS_W / BASE_WIDTH
        font_size    = round(BASE_FONT_SIZE * scale)
        line_spacing = round(BASE_LINE_SPACING * scale)

        font = ImageFont.truetype(cfg["font"], size=font_size)
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
            x    = (CANVAS_W - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, font=font, fill=cfg["text_colour"])
            y += line_h + line_spacing

    canvas.convert("RGB").save(cfg["output"], format="PNG")
    print(f"Saved {cfg['output']} — {canvas.size}")


# ── Config-mode helpers ───────────────────────────────────────────────────────

def _normalise_hex(value, field):
    """Return '#RRGGBB'; exit with a clear error if the value isn't a valid 6-digit hex."""
    s = str(value).strip().lstrip("#")
    if len(s) != 6 or not all(c in "0123456789abcdefABCDEF" for c in s):
        sys.exit(f"Error: {field} value '{value}' is not a valid 6-digit hex colour.")
    return f"#{s.upper()}"


def _resolve_input(input_dir, basename):
    """Return the single matching file for basename; exit if zero or more than one found."""
    found = [p for p in input_dir.iterdir()
             if p.stem == basename and p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    if not found:
        sys.exit(
            f"Error: no file found for basename '{basename}' in {input_dir}\n"
            f"  Looked for: {basename}.jpg / .jpeg / .png (any case)"
        )
    if len(found) > 1:
        sys.exit(
            f"Error: ambiguous input for basename '{basename}' — multiple files found:\n"
            + "\n".join(f"  {p}" for p in found)
        )
    return found[0]


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

    font_cfg      = raw.get("font") or {}
    font_path     = str(_res(font_cfg["path"])) if font_cfg.get("path") else None
    font_axes_raw = font_cfg.get("axes")
    font_axes     = [float(v) for v in str(font_axes_raw).split(",")] if font_axes_raw else None

    if any(str(e.get("text", "")).strip() for e in entries) and not font_path:
        sys.exit("Error: 'font.path' is required when any screenshot has text.")

    output_dir.mkdir(parents=True, exist_ok=True)

    for i, entry in enumerate(entries):
        label = f"screenshots[{i}]"
        for key in ("inputBasename", "backgroundColour", "textColour"):
            if key not in entry:
                sys.exit(f"Error: {label} is missing required key '{key}'.")

        basename   = entry["inputBasename"]
        label      = f"screenshots[{i}] ('{basename}')"
        input_file = _resolve_input(input_dir, basename)
        bg         = _normalise_hex(entry["backgroundColour"], f"{label}.backgroundColour")
        text_col   = _normalise_hex(entry["textColour"],       f"{label}.textColour")
        lines      = [l.strip() for l in str(entry.get("text", "")).split("|") if l.strip()]

        render({
            "input":         str(input_file),
            "output":        str(output_dir / f"screenshot-{i + 1}-{basename}_processed.png"),
            "bg":            bg,
            "lines":         lines,
            "text_colour":   text_col,
            "font":          font_path,
            "font_axes":     font_axes,
            "screen_w":      DEFAULT_SCREEN_W,
            "bezel":         DEFAULT_BEZEL,
            "radius":        DEFAULT_RADIUS,
            "bottom_margin": DEFAULT_BOTTOM_MARGIN,
            "top_padding":   DEFAULT_TOP_PADDING,
            "frame_colour":  DEFAULT_FRAME_COLOUR,
        })

    ipad_in_raw  = raw.get("ipadInputDirectory")
    ipad_out_raw = raw.get("ipadOutputDirectory")
    if bool(ipad_in_raw) != bool(ipad_out_raw):
        missing = "ipadOutputDirectory" if ipad_in_raw else "ipadInputDirectory"
        sys.exit(f"Error: '{missing}' must be set when the other iPad directory key is set.")
    if ipad_in_raw and ipad_out_raw:
        ipad_in  = _res(ipad_in_raw)
        ipad_out = _res(ipad_out_raw)
        if not ipad_in.is_dir():
            sys.exit(f"Error: ipadInputDirectory not found: {ipad_in}")
        images = sorted(p for p in ipad_in.iterdir()
                        if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
        if not images:
            sys.exit(f"Error: no images found in ipadInputDirectory: {ipad_in}")
        ipad_out.mkdir(parents=True, exist_ok=True)
        for img_path in images:
            out_path = ipad_out / f"{img_path.stem}.png"
            result = fit_and_pad(img_path, IPAD_W, IPAD_H, IPAD_PAD_COLOUR)
            result.save(str(out_path), format="PNG")
            print(f"Saved {out_path} — {result.size}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Produce a 1284×2778 App Store screenshot from a raw iOS screenshot."
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
    parser.add_argument("--screen-width",   type=int, default=DEFAULT_SCREEN_W,
                        help=f"Screenshot width inside bezel in px (default: {DEFAULT_SCREEN_W}).")
    parser.add_argument("--bezel",          type=int, default=DEFAULT_BEZEL,
                        help=f"Bezel border thickness in px (default: {DEFAULT_BEZEL}).")
    parser.add_argument("--radius",         type=int, default=DEFAULT_RADIUS,
                        help=f"Inner corner radius in px (default: {DEFAULT_RADIUS}).")
    parser.add_argument("--bottom-margin",  type=int, default=DEFAULT_BOTTOM_MARGIN,
                        help=f"Gap below phone in px (default: {DEFAULT_BOTTOM_MARGIN}).")
    parser.add_argument("--top-padding",    type=int, default=DEFAULT_TOP_PADDING,
                        help=f"Minimum gap above text in px (default: {DEFAULT_TOP_PADDING}).")
    parser.add_argument("--frame-colour",   default=DEFAULT_FRAME_COLOUR,
                        help=f"Bezel colour hex (default: '{DEFAULT_FRAME_COLOUR}').")

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
