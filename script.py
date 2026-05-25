import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── Canvas ────────────────────────────────────────────────────────────────────

CANVAS_W, CANVAS_H = 1284, 2778

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

    canvas.save(cfg["output"], format="PNG")
    print(f"Saved {cfg['output']} — {canvas.size}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Produce a 1284×2778 App Store screenshot from a raw iOS screenshot."
    )
    parser.add_argument("input",
                        help="Path to the raw screenshot (JPEG/PNG).")
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
