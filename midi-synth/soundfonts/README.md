# SoundFonts

This directory is where `.sf2` SoundFont files live for high-quality MIDI rendering.
Binary `.sf2` files are not committed to the repo because of their size.

## Auto-Download (default behaviour)

`scripts/render.py` automatically downloads **GeneralUser GS v1.471** (~31 MB) into this
directory on first run if no `.sf2` is found. No manual setup required.

To override:

```bash
# Opt out — use built-in sine-wave synthesis instead
py -3.12 scripts/render.py "song.mid" --no-auto-download

# Use a custom URL
py -3.12 scripts/render.py "song.mid" --soundfont-url "https://example.com/MyFont.sf2"

# Or via environment variable
MIDI_SYNTH_SOUNDFONT_URL="https://example.com/MyFont.sf2" \
  py -3.12 scripts/render.py "song.mid"
```

## Manual install

If auto-download is blocked (offline, firewall) drop any `.sf2` here and `render.py` picks it up:

| Name | Size | Quality | Download |
|------|------|---------|----------|
| GeneralUser GS | ~31 MB | Good all-around GM (default) | https://archive.org/details/free-soundfonts-sf2-2019-04 |
| MuseScore General | ~215 MB | High-quality GM (built-in fallback) | https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/ |
| FluidR3 GM | ~142 MB | Classic GM | https://member.keymusician.com/Member/FluidR3_GM/index.html |
| FatBoy | ~316 MB | Full GM/GS, very detailed | https://fatboy.site/ |

You can also pass `--soundfont path/to/font.sf2` to point at a SoundFont anywhere on disk.

## Without a SoundFont

If no SoundFont is found and auto-download is disabled, `render.py` falls back to built-in
sine-wave synthesis (lower quality, always works, no extra dependencies).
