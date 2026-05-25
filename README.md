# app-screenshots-tool

Generates App Store screenshots (1284×2778 px) from a raw iOS screenshot. Places the screenshot inside a simple iPhone-style bezel, centres it on a coloured background, and adds brand text above it.

## Usage

```bash
python script.py <raw_screenshot> --font <font.ttf> [options]
```

### Required

| Argument | Description |
|---|---|
| `raw_screenshot` | Path to the raw iOS screenshot (JPEG or PNG). |
| `--font <path>` | Path to a `.ttf` font file. Required when `--text` is provided. |

### Common options

| Option | Default | Description |
|---|---|---|
| `--text "Line one\|Line two"` | _(none)_ | Text to display above the phone, lines separated by `\|`. |
| `--text-colour "#000000"` | `#000000` | Text colour. |
| `--bg "#FFFFFF"` | `#FFFFFF` | Background colour. |
| `--font-axes "600,100"` | _(none)_ | Variable font axes as comma-separated values (e.g. Weight, Width for Fredoka). |
| `-o output.png` | `<input_stem>_final.png` | Output path. Defaults to the input filename with `_final.png` appended. |

### Frame-tuning options

| Option | Default | Description |
|---|---|---|
| `--screen-width <px>` | `940` | Width of the screenshot inside the bezel. |
| `--bezel <px>` | `26` | Bezel border thickness. |
| `--radius <px>` | `90` | Inner corner radius of the screen. |
| `--bottom-margin <px>` | `120` | Gap between the phone bottom and the canvas edge. |
| `--top-padding <px>` | `40` | Minimum gap between the canvas top and the text. |
| `--frame-colour "#000000"` | `#000000` | Bezel colour. |

## Example

```bash
python script.py skintracker/skintracker-1.jpeg \
  --bg "#FFFFFF" \
  --text "Track every breakout|Watch your skin improve" \
  --font "skintracker/Fredoka-VariableFont_wdth,wght.ttf" \
  --font-axes "600,100" \
  -o skintracker/skintracker-1_final.png
```

## Requirements

- Python 3
- [Pillow](https://pillow.readthedocs.io/) (`pip install pillow`)
