# SoundFonts

This directory is where `.sf2` SoundFont files should be placed for high-quality MIDI rendering.

SoundFont binary files are not included in this repository due to their large size.

## Recommended SoundFonts

| Name | Size | Quality | Download |
|------|------|---------|----------|
| GeneralUser GS | ~30 MB | Good all-around GM | https://schristiancollins.com/generaluser.php |
| FluidR3 GM | ~142 MB | High quality GM | https://member.keymusician.com/Member/FluidR3_GM/index.html |
| FatBoy | ~316 MB | Full GM/GS, very detailed | https://fatboy.site/ |

## Usage

Once you have downloaded a `.sf2` file, place it in this directory. The `render.py` script
will auto-detect it:

```bash
# Auto-detect any .sf2 in this directory
py -3.12 scripts/render.py "song.mid" --mp3

# Or specify explicitly
py -3.12 scripts/render.py "song.mid" --soundfont "soundfonts/GeneralUser_GS.sf2" --mp3
```

## Without a SoundFont

If no SoundFont is found, `render.py` falls back to built-in sine-wave synthesis
(lower quality but always works, no extra dependencies required).
