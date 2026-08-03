# App screenshots tool

Generates App Store screenshots (1284×2778 px) from provided iOS screenshots. 

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
uv run script.py --config banyan-flashcards/config.yaml
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
Every `.png`, `.jpg`, or `.jpeg` in the input directory is scaled to fit inside
2064×2752 (preserving aspect ratio) and centred on a white canvas — no bezel or
text. Output files keep their original stem with a `.png` extension.

```yaml
ipadInputDirectory: input-ipad
ipadOutputDirectory: output-ipad
```

### Dependencies

Managed via `pyproject.toml` / `uv.lock`:

- [Pillow](https://pillow.readthedocs.io/)
- [PyYAML](https://pyyaml.org/)
