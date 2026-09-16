# App screenshots tool

Generates App Store screenshots from provided iOS screenshots: 1284×2778 px for iPhone, 2064×2752 px for iPad.

## Sample output

- Background of a chosen colour.
- Text using the chosen colour and in a chosen font, having the configured font axes, and with the text having line breaks at the chosen places.
- Screenshot fitted inside an iPhone bezel below.

<img src="sample-outputs/skintracker-trends.png" width="300"> <img src="sample-outputs/banyan-sentence.png" width="300">

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```
uv sync
```

## Usage

```
uv run script.py --config banyan-flashcards/main/config.yaml
```

```
uv run script.py --config skintracker/config.yaml
```

## Example configuration

This is the configuration for my skintracker app:

- Input file basenames don't have file extensions, they find based on the basename.
- Colours are hex strings, listed separately from the screenshots — see [Fixed colour sequence](#fixed-colour-sequence).
- Vertical bars indicate line breaks for the text.
- Font axes are based on the tvar axis order, which may or may not match the variable font's filename.
- Output files will be prefixed to preserve the order of items in the yaml list.
- Each run deletes and recreates the output directories first, so the output only ever contains the files the config produces. The tool refuses to run if an output directory contains the config, an input directory, or the font.

```yaml
inputDirectory: input
outputDirectory: output
font:
  path: Fredoka-VariableFont_wdth,wght.ttf
  axes: "550,105"
colours:
- backgroundColour: FEF6F0
  textColour: "3B1F14"
- backgroundColour: EDF3FC
  textColour: "0E2646"
- backgroundColour: F4EFF9
  textColour: "2C1545"
- backgroundColour: F0F7F4
  textColour: "163D2C"
screenshots:
- inputBasename: home
  text: "Your simple home|for acne recovery"
- inputBasename: trends
  text: "Understand the trends|that lead to outbreaks"
- inputBasename: gallery
  text: "Save photos to see|on your progress"
- inputBasename: record
  text: "Record regularly|to stay focused"
```

### Fixed colour sequence

The top-level `colours` list is positional: the first entry always applies to the
first screenshot, whichever screenshot that now is. So the colour sequence stays
still while the screenshots and their text are reordered or copy-pasted around —
which is the point of keeping it out of the `screenshots` list.

The list must be the same length as `screenshots`, and each entry needs both
`backgroundColour` and `textColour`.

Colours may instead be set on each screenshot entry, as an older config might do:

```yaml
screenshots:
- inputBasename: home
  backgroundColour: FEF6F0
  textColour: "3B1F14"
  text: "Your simple home|for acne recovery"
```

Those travel with the screenshot when it moves. The two forms can't be combined —
if `colours` is present, a screenshots entry setting `backgroundColour` or
`textColour` is an error rather than one form silently winning.

### iPad screenshots

To also produce iPad App Store screenshots (2064×2752 px), add the optional
`ipadInputDirectory` and `ipadOutputDirectory` keys. Both must be set together.

```yaml
ipadInputDirectory: input-ipad
ipadOutputDirectory: output-ipad
```

iPad screenshots get the same styling as iPhone screenshots — coloured
background, text, and bezel — and reuse the same `screenshots` list. There is no
separate iPad list:

- Each `screenshots` entry is matched to an iPad image by `inputBasename`, so an
  iPad screenshot carries the same text and colour as its iPhone twin.
- Entries with no iPad image are passed over, and iPad images that match no entry
  are skipped with a note printed to the console.
- Output files are numbered 1..N over the iPad screenshots actually produced, in
  the order the entries appear in `screenshots`, and are named like the iPhone
  ones: `screenshot-1-progress_processed.png`.

Every frame measurement is scaled from the iPhone canvas by the ratio of canvas
widths, so the bezel fills the same 77% of the width on both devices.

Give the tool iPad screenshots captured at 2064×2752 — the 13-inch iPad size. A
source that is taller in proportion, such as an 11-inch iPad capture, produces a
taller bezel that leaves too little room, and the text will overlap it.

### Dependencies

Managed via `pyproject.toml` / `uv.lock`:

- [Pillow](https://pillow.readthedocs.io/)
- [PyYAML](https://pyyaml.org/)
