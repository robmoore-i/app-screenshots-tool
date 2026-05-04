import argparse
import os

from PIL import Image, ImageDraw, ImageFont

# ── Configuration ────────────────────────────────────────────────────────────

FONT_PATH = "/Users/rob/Installed/claude/Fraunces-VariableFont_SOFT,WONK,opsz,wght.ttf"

# Font variation axes order: [Optical Size, Weight, Softness, Wonky]
# Weight range: 100 (thin) – 900 (black). Website default is 900.
FONT_AXES = [9, 400, 0, 1]

# Base font size and spacing were tuned at 922px wide, then scaled to actual image width.
BASE_WIDTH = 922
BASE_FONT_SIZE = 64
BASE_LINE_SPACING = 14

# ── Screenshot definitions ───────────────────────────────────────────────────
# top_area: height in pixels (at BASE_WIDTH scale) of the background area
# above the phone mockup where the text is centred vertically.
# text_colour: '#000000' for black, '#FFFFFF' for white.

SCREENSHOTS = [
    {
        "input":  "ios_1_1.png",
        "output": "ios_1_1_text.png",
        "lines": [
            "Language learning that",
            "fits into your schedule using",
            "flashcard notifications",
        ],
        "text_colour": "#000000",
        "top_area": 330,
    },
    {
        "input":  "ios_1_2.png",
        "output": "ios_1_2_text.png",
        "lines": [
            "Simple and immersive.",
            "Make constant progress",
            "without the hassle",
        ],
        "text_colour": "#000000",
        "top_area": 390,
    },
    {
        "input":  "ios_1_3.png",
        "output": "ios_1_3_text.png",
        "lines": [
            "Add vocabulary,",
            "learn passively",
        ],
        "text_colour": "#000000",
        "top_area": 370,
    },
    {
        "input":  "ios_1_4.png",
        "output": "ios_1_4_text.png",
        "lines": [
            "Practice using your words",
            "in real sentences,",
            "regularly and easily",
        ],
        "text_colour": "#FFFFFF",
        "top_area": 370,
    },
    {
        "input":  "ios_1_5.png",
        "output": "ios_1_5_text.png",
        "lines": [
            "Fine tune your",
            "learning experience",
        ],
        "text_colour": "#000000",
        "top_area": 355,
    },
]

# ── Rendering ────────────────────────────────────────────────────────────────

def render(cfg):
    img = Image.open(cfg["input"])
    img_width, _ = img.size
    draw = ImageDraw.Draw(img)

    # Scale font size and spacing proportionally to actual image width
    scale = img_width / BASE_WIDTH
    font_size = round(BASE_FONT_SIZE * scale)
    line_spacing = round(BASE_LINE_SPACING * scale)

    font = ImageFont.truetype(FONT_PATH, size=font_size)
    font.set_variation_by_axes(FONT_AXES)

    # Use a fixed line height based on reference chars with ascenders & descenders,
    # so spacing is consistent regardless of which characters appear in each line.
    ref_bbox = draw.textbbox((0, 0), "Ag", font=font)
    fixed_line_height = ref_bbox[3] - ref_bbox[1]

    lines = cfg["lines"]
    total_h = fixed_line_height * len(lines) + line_spacing * (len(lines) - 1)

    scaled_top = round(cfg["top_area"] * scale)
    y = (scaled_top - total_h) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (img_width - w) // 2
        draw.text((x, y), line, font=font, fill=cfg["text_colour"])
        y += fixed_line_height + line_spacing

    img.save(cfg["output"], format="PNG")
    print(f"Saved {cfg['output']} — {img.size}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("screenshots_dir", nargs="?", default=".", help="Path to directory containing iOS screenshots")
    parser.add_argument("--output-dir", default=".", help="Directory to write output files into")
    args = parser.parse_args()
    d = args.screenshots_dir

    for cfg in SCREENSHOTS:
        cfg = {**cfg, "input": os.path.join(d, cfg["input"]), "output": os.path.join(args.output_dir, cfg["output"])}
        render(cfg)
