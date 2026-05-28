# App screenshots tool

Generates App Store screenshots (1284×2778 px) from a raw iOS screenshot. Places the screenshot inside a simple iPhone-style bezel, centres it on a coloured background, and adds brand text above it.

## Usage

```
python3 script.py --config banyan-flashcards/config.yaml
```

```
python3 script.py --config skintracker/config.yaml
```

### Dependencies

- Python 3
- [Pillow](https://pillow.readthedocs.io/) (`pip install pillow`)
- [PyYAML](https://pyyaml.org/) (`pip install pyyaml`)
