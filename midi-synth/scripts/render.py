#!/usr/bin/env python3
"""Render MIDI/MusicXML to WAV/MP3 with analysis-aware cleaning and dynamics."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

SOUNDFONT_DIR = Path(__file__).parent.parent / "soundfonts"

# Auto-download targets. First entry is the default (smaller); second is a fallback.
# Override via the MIDI_SYNTH_SOUNDFONT_URL env var or --soundfont-url flag.
DEFAULT_SOUNDFONTS = [
    {
        "name": "GeneralUser_GS_v1.471.sf2",
        "url": "https://archive.org/download/free-soundfonts-sf2-2019-04/GeneralUser%20GS%20v1.471.sf2",
        "size": 31_281_186,
    },
    {
        "name": "MuseScore_General.sf2",
        "url": "https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf2",
        "size": 215_614_036,
    },
]

SCALE_DEGREES = {
    'C major': {0, 2, 4, 5, 7, 9, 11}, 'C minor': {0, 2, 3, 5, 7, 8, 10},
    'C# major': {1, 3, 5, 6, 8, 10, 0}, 'C# minor': {1, 3, 4, 6, 8, 9, 11},
    'D major': {2, 4, 6, 7, 9, 11, 1}, 'D minor': {2, 4, 5, 7, 9, 10, 0},
    'D# major': {3, 5, 7, 8, 10, 0, 2}, 'D# minor': {3, 5, 6, 8, 10, 11, 1},
    'E major': {4, 6, 8, 9, 11, 1, 3}, 'E minor': {4, 6, 7, 9, 11, 0, 2},
    'F major': {5, 7, 9, 10, 0, 2, 4}, 'F minor': {5, 7, 8, 10, 0, 1, 3},
    'F# major': {6, 8, 10, 11, 1, 3, 5}, 'F# minor': {6, 8, 9, 11, 1, 2, 4},
    'G major': {7, 9, 11, 0, 2, 4, 6}, 'G minor': {7, 9, 10, 0, 2, 3, 5},
    'G# major': {8, 10, 0, 1, 3, 5, 7}, 'G# minor': {8, 10, 11, 1, 3, 4, 6},
    'A major': {9, 11, 1, 2, 4, 6, 8}, 'A minor': {9, 11, 0, 2, 4, 5, 7},
    'A# major': {10, 0, 2, 3, 5, 7, 9}, 'A# minor': {10, 0, 1, 3, 5, 6, 8},
    'B major': {11, 1, 3, 4, 6, 8, 10}, 'B minor': {11, 1, 2, 4, 6, 7, 9},
}


def ensure_deps():
    missing = []
    for mod, pkg in {'pretty_midi': 'pretty_midi', 'numpy': 'numpy', 'soundfile': 'soundfile'}.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"Installing: {', '.join(missing)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet'] + missing,
                              stdout=subprocess.DEVNULL)


def load_analysis(path):
    if not path:
        return None
    p = Path(path).resolve()
    if not p.exists():
        return None
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_analysis(input_path):
    base = Path(input_path).resolve()
    for c in [base.with_name(base.stem + '_analysis.json'),
              base.parent / (base.stem.rsplit('.', 1)[0] + '_analysis.json')]:
        if c.exists():
            return c
    for f in base.parent.glob('*_analysis.json'):
        return f
    return None


def load_input(input_path):
    """Load MIDI or MusicXML, return pretty_midi object."""
    import pretty_midi
    p = Path(input_path).resolve()
    suffix = p.suffix.lower()

    if suffix in ('.musicxml', '.xml', '.mxl'):
        print(f"  Converting MusicXML to MIDI...")
        from music21 import converter
        score = converter.parse(str(p))
        tmp = Path(tempfile.mktemp(suffix='.mid'))
        score.write('midi', fp=str(tmp))
        midi = pretty_midi.PrettyMIDI(str(tmp))
        tmp.unlink()
        return midi
    else:
        return pretty_midi.PrettyMIDI(str(p))


def clean_midi(midi, min_velocity=40, min_duration=0.05, key_str=None, key_vel_thresh=60):
    """Remove ghost notes from all instruments. Returns total removed count."""
    key_scale = SCALE_DEGREES.get(key_str)
    total_before = 0
    total_after = 0

    for inst in midi.instruments:
        total_before += len(inst.notes)
        cleaned = []
        for n in inst.notes:
            if n.velocity < min_velocity:
                continue
            if (n.end - n.start) < min_duration:
                continue
            if key_scale and (n.pitch % 12) not in key_scale and n.velocity < key_vel_thresh:
                continue
            cleaned.append(n)
        inst.notes = cleaned
        total_after += len(cleaned)

    removed = total_before - total_after
    if removed > 0:
        print(f"  Cleaned: {total_before} -> {total_after} notes ({removed} ghost notes removed)")
    return removed


def apply_modifications(midi, tempo_scale=1.0, transpose=0, instrument=None):
    """Apply tempo/pitch/instrument changes in-place."""
    if tempo_scale != 1.0:
        for inst in midi.instruments:
            for note in inst.notes:
                note.start /= tempo_scale
                note.end /= tempo_scale
            for cc in inst.control_changes:
                cc.time /= tempo_scale
            for pb in inst.pitch_bends:
                pb.time /= tempo_scale

    if transpose != 0:
        for inst in midi.instruments:
            if not inst.is_drum:
                for note in inst.notes:
                    note.pitch = max(0, min(127, note.pitch + transpose))

    if instrument is not None:
        for inst in midi.instruments:
            if not inst.is_drum:
                inst.program = instrument


def find_soundfont(explicit_path=None):
    if explicit_path:
        p = Path(explicit_path).resolve()
        if p.exists():
            return p
    if SOUNDFONT_DIR.exists():
        for sf in SOUNDFONT_DIR.glob("*.sf2"):
            return sf
    for d in [Path.home() / "soundfonts", Path("C:/soundfonts"),
              Path("/usr/share/sounds/sf2"), Path("/usr/share/soundfonts")]:
        if d.exists():
            for sf in d.glob("*.sf2"):
                return sf
    return None


def download_soundfont(target_dir=SOUNDFONT_DIR, url=None, name=None):
    """Download a default SoundFont into target_dir. Returns path on success, None on failure.

    Resolution order for url/name:
      1. explicit url/name args
      2. MIDI_SYNTH_SOUNDFONT_URL / MIDI_SYNTH_SOUNDFONT_NAME env vars
      3. DEFAULT_SOUNDFONTS list (tried in order)
    """
    target_dir.mkdir(parents=True, exist_ok=True)

    if url:
        candidates = [{"name": name or Path(url).name, "url": url, "size": 0}]
    elif os.environ.get("MIDI_SYNTH_SOUNDFONT_URL"):
        env_url = os.environ["MIDI_SYNTH_SOUNDFONT_URL"]
        env_name = os.environ.get("MIDI_SYNTH_SOUNDFONT_NAME") or Path(env_url).name
        candidates = [{"name": env_name, "url": env_url, "size": 0}]
    else:
        candidates = DEFAULT_SOUNDFONTS

    for cand in candidates:
        dest = target_dir / cand["name"]
        if dest.exists() and dest.stat().st_size > 1_000_000:
            return dest

        size_mb = cand["size"] / 1_048_576 if cand["size"] else 0
        size_str = f" (~{size_mb:.0f} MB)" if size_mb else ""
        print(f"  Downloading SoundFont: {cand['name']}{size_str}")
        print(f"    From: {cand['url']}")
        print(f"    To:   {dest}")

        tmp = dest.with_suffix(dest.suffix + ".part")
        try:
            with urllib.request.urlopen(cand["url"], timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                last_pct = -1
                with open(tmp, "wb") as out:
                    while True:
                        chunk = resp.read(1024 * 256)
                        if not chunk:
                            break
                        out.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = int(downloaded * 100 / total)
                            if pct != last_pct and pct % 10 == 0:
                                print(f"    {pct}% ({downloaded // 1_048_576} / {total // 1_048_576} MB)")
                                last_pct = pct
            if tmp.stat().st_size < 1_000_000:
                tmp.unlink(missing_ok=True)
                print(f"    Failed: file too small")
                continue
            tmp.replace(dest)
            print(f"  Downloaded: {dest.name}")
            return dest
        except Exception as e:
            tmp.unlink(missing_ok=True)
            print(f"    Failed: {e}")
            continue

    print("  All SoundFont download candidates failed.")
    print("  Manual download instructions: see soundfonts/README.md")
    return None


def has_fluidsynth_lib():
    try:
        import fluidsynth
        fs = fluidsynth.Synth()
        fs.delete()
        return True
    except Exception:
        return False


def render_fluidsynth_lib(midi, output_path, sf_path, sample_rate=44100):
    import numpy as np
    import soundfile as sf
    audio = midi.fluidsynth(fs=sample_rate, sf2_path=str(sf_path))
    if audio.ndim == 1:
        audio = np.column_stack([audio, audio])
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.95
    sf.write(str(output_path), audio, sample_rate)
    return True


def render_fluidsynth_cli(midi_path, output_path, sf_path, sample_rate=44100):
    try:
        subprocess.run(['fluidsynth', '-ni', str(sf_path), str(midi_path),
                        '-F', str(output_path), '-r', str(sample_rate)],
                       check=True, capture_output=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def render_builtin(midi, output_path, sample_rate=44100):
    import numpy as np
    import soundfile as sf
    audio = midi.synthesize(fs=sample_rate)
    if audio.ndim == 1:
        audio = np.column_stack([audio, audio])
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.95
    sf.write(str(output_path), audio, sample_rate)
    return True


def wav_to_mp3(wav_path, mp3_path):
    try:
        subprocess.run(['ffmpeg', '-y', '-i', str(wav_path), '-b:a', '192k',
                        '-loglevel', 'error', str(mp3_path)],
                       check=True, capture_output=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def list_instruments():
    gm = [
        "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano",
        "Honky-tonk Piano", "Electric Piano 1", "Electric Piano 2", "Harpsichord",
        "Clavi", "Celesta", "Glockenspiel", "Music Box", "Vibraphone", "Marimba",
        "Xylophone", "Tubular Bells", "Dulcimer", "Drawbar Organ", "Percussive Organ",
        "Rock Organ", "Church Organ", "Reed Organ", "Accordion", "Harmonica",
        "Tango Accordion", "Nylon Guitar", "Steel Guitar", "Jazz Guitar",
        "Clean Electric Guitar", "Muted Electric Guitar", "Overdriven Guitar",
        "Distortion Guitar", "Guitar Harmonics", "Acoustic Bass", "Finger Bass",
        "Pick Bass", "Fretless Bass", "Slap Bass 1", "Slap Bass 2", "Synth Bass 1",
        "Synth Bass 2", "Violin", "Viola", "Cello", "Contrabass", "Tremolo Strings",
        "Pizzicato Strings", "Orchestral Harp", "Timpani", "String Ensemble 1",
        "String Ensemble 2", "Synth Strings 1", "Synth Strings 2", "Choir Aahs",
        "Voice Oohs", "Synth Voice", "Orchestra Hit", "Trumpet", "Trombone", "Tuba",
        "Muted Trumpet", "French Horn", "Brass Section", "Synth Brass 1",
        "Synth Brass 2", "Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax",
        "Oboe", "English Horn", "Bassoon", "Clarinet", "Piccolo", "Flute", "Recorder",
        "Pan Flute", "Blown Bottle", "Shakuhachi", "Whistle", "Ocarina",
        "Lead 1 (Square)", "Lead 2 (Sawtooth)", "Lead 3 (Calliope)", "Lead 4 (Chiff)",
        "Lead 5 (Charang)", "Lead 6 (Voice)", "Lead 7 (Fifths)", "Lead 8 (Bass+Lead)",
        "Pad 1 (New Age)", "Pad 2 (Warm)", "Pad 3 (Polysynth)", "Pad 4 (Choir)",
        "Pad 5 (Bowed)", "Pad 6 (Metallic)", "Pad 7 (Halo)", "Pad 8 (Sweep)",
    ]
    print("General MIDI Instruments (use number with --instrument):\n")
    for i, name in enumerate(gm):
        print(f"  {i:3d}  {name}")


def main():
    parser = argparse.ArgumentParser(description='Render MIDI/MusicXML to WAV/MP3 with cleaning')
    parser.add_argument('input', nargs='?', help='Input MIDI (.mid) or MusicXML (.musicxml)')
    parser.add_argument('-o', '--output', help='Output WAV file')
    parser.add_argument('--analysis', '-a', help='Analysis JSON (auto-detected if omitted)')
    parser.add_argument('--mp3', action='store_true', help='Also produce MP3')
    parser.add_argument('--soundfont', '--sf', help='Path to .sf2 SoundFont')
    parser.add_argument('--soundfont-url', help='URL to download a custom SoundFont (overrides defaults)')
    parser.add_argument('--no-auto-download', action='store_true',
                        help='Disable auto-download; fall back to built-in synthesis if no .sf2 found')
    parser.add_argument('--tempo', type=float, default=1.0, help='Tempo scale (0.5=half, 2.0=double)')
    parser.add_argument('--transpose', type=int, default=0, help='Transpose semitones')
    parser.add_argument('--instrument', type=int, help='Override instruments with GM number (0-127)')
    parser.add_argument('--min-velocity', type=int, default=40,
                        help='Remove notes below this velocity (default: 40)')
    parser.add_argument('--min-duration', type=float, default=0.05,
                        help='Remove notes shorter than this in seconds (default: 0.05)')
    parser.add_argument('--no-clean', action='store_true', help='Skip ghost note removal')
    parser.add_argument('--no-key-filter', action='store_true', help='Disable key-based filtering')
    parser.add_argument('--sample-rate', type=int, default=44100, help='Sample rate (default: 44100)')
    parser.add_argument('--list-instruments', action='store_true', help='List GM instruments')
    args = parser.parse_args()

    if args.list_instruments:
        list_instruments()
        return
    if not args.input:
        parser.error("input file is required")

    ensure_deps()

    src = Path(args.input).resolve()
    if not src.exists():
        print(f"Error: not found: {src}", file=sys.stderr)
        sys.exit(1)

    # Load analysis
    analysis_path = args.analysis or find_analysis(src)
    analysis = load_analysis(analysis_path) if analysis_path else None
    if analysis:
        print(f"  Analysis: {analysis_path}")
        print(f"  Key: {analysis.get('key', '?')} | Tempo: {analysis.get('tempo_bpm', '?')} BPM")

    # Load input
    midi = load_input(src)
    note_count = sum(len(inst.notes) for inst in midi.instruments)
    print(f"  Loaded: {note_count} notes")

    # Clean ghost notes
    if not args.no_clean:
        key_str = None
        if analysis and not args.no_key_filter:
            key_str = analysis.get('key')
        clean_midi(midi, args.min_velocity, args.min_duration, key_str)

    # Apply modifications
    apply_modifications(midi, args.tempo, args.transpose, args.instrument)

    # Save cleaned MIDI to temp file for CLI-based renderers
    tmp_midi = Path(tempfile.mktemp(suffix='.mid'))
    midi.write(str(tmp_midi))

    wav_path = Path(args.output).resolve() if args.output else src.with_suffix('.wav')
    wav_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n  Rendering: {src.name}")
    if args.tempo != 1.0:
        print(f"  Tempo: {args.tempo}x")
    if args.transpose != 0:
        print(f"  Transpose: {args.transpose:+d} semitones")

    sf_path = find_soundfont(args.soundfont)
    if not sf_path and not args.no_auto_download:
        sf_path = download_soundfont(url=args.soundfont_url)

    success = False
    method = "built-in (sine waves)"

    if sf_path and has_fluidsynth_lib():
        try:
            success = render_fluidsynth_lib(midi, wav_path, sf_path, args.sample_rate)
            method = f"FluidSynth + {sf_path.name}"
        except Exception as e:
            print(f"  FluidSynth lib failed: {e}")

    if not success and sf_path:
        success = render_fluidsynth_cli(tmp_midi, wav_path, sf_path, args.sample_rate)
        if success:
            method = f"FluidSynth CLI + {sf_path.name}"

    if not success:
        if not sf_path:
            print("  No SoundFont found. Using built-in synthesis.")
        render_builtin(midi, wav_path, args.sample_rate)

    tmp_midi.unlink(missing_ok=True)

    print(f"  Method: {method}")
    print(f"  WAV: {wav_path}")

    if args.mp3:
        mp3_path = wav_path.with_suffix('.mp3')
        if wav_to_mp3(wav_path, mp3_path):
            print(f"  MP3: {mp3_path}")
        else:
            print("  MP3 failed (ffmpeg not found)")

    print("  Done!")


if __name__ == '__main__':
    main()
