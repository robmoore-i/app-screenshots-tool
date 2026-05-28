# App screenshots tool

Generates App Store screenshots (1284×2778 px) from a raw iOS screenshot. Places the screenshot inside a simple iPhone-style bezel, centres it on a coloured background, and adds styled text above it.

## Sample output

<img src="sample-outputs/skintracker-trends.png" width="300"> <img src="sample-outputs/banyan-sentence.png" width="300">

## Usage

```
python3 script.py --config banyan-flashcards/config.yaml
```

```
python3 script.py --config skintracker/config.yaml
```

### Dependencies

- Python 3
- [Pillow](https://pillow.readthedocs.io/)
- [PyYAML](https://pyyaml.org/)
