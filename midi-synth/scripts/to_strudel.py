#!/usr/bin/env python3
"""Convert MIDI/MusicXML to Strudel live-coding patterns with analysis-aware cleaning."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

NOTE_NAMES = ['c', 'db', 'd', 'eb', 'e', 'f', 'gb', 'g', 'ab', 'a', 'bb', 'b']

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

GM_TO_STRUDEL = {
    range(0, 8): 'piano', range(8, 16): 'piano', range(16, 24): 'organ',
    range(24, 32): 'guitar', range(32, 40): 'bass', range(40, 56): 'sawtooth',
    range(56, 64): 'square', range(64, 72): 'triangle', range(72, 80): 'sine',
    range(80, 88): 'square', range(88, 96): 'sawtooth', range(96, 128): 'triangle',
}


def ensure_deps():
    missing = []
    for mod, pkg in {'pretty_midi': 'pretty_midi', 'numpy': 'numpy'}.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet'] + missing,
                              stdout=subprocess.DEVNULL)


def note_name(midi_num):
    return f"{NOTE_NAMES[midi_num % 12]}{midi_num // 12 - 1}"


def strudel_sound(program, is_drum=False):
    if is_drum:
        return 'metal'
    for rng, sound in GM_TO_STRUDEL.items():
        if program in rng:
            return sound
    return 'triangle'


def load_analysis(path):
    """Load analysis JSON for tempo, key, dynamics."""
    if not path:
        return None
    p = Path(path).resolve()
    if not p.exists():
        # Try auto-detecting: look for *_analysis.json next to input
        return None
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_analysis(input_path):
    """Auto-detect analysis JSON next to the input file."""
    base = Path(input_path).resolve()
    candidates = [
        base.with_name(base.stem + '_analysis.json'),
        base.parent / (base.stem.rsplit('.', 1)[0] + '_analysis.json'),
    ]
    for c in candidates:
        if c.exists():
            return c
    # Search parent dir for any analysis json
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
        import tempfile
        tmp = Path(tempfile.mktemp(suffix='.mid'))
        score.write('midi', fp=str(tmp))
        midi = pretty_midi.PrettyMIDI(str(tmp))
        tmp.unlink()
        return midi
    else:
        return pretty_midi.PrettyMIDI(str(p))


def clean_notes(notes, min_velocity=40, min_duration=0.05, key_scale=None,
                key_velocity_thresh=60):
    """Filter ghost notes based on velocity, duration, and key."""
    cleaned = []
    removed = {'velocity': 0, 'duration': 0, 'key': 0}

    for n in notes:
        if n.velocity < min_velocity:
            removed['velocity'] += 1
            continue
        dur = n.end - n.start
        if dur < min_duration:
            removed['duration'] += 1
            continue
        if key_scale is not None and (n.pitch % 12) not in key_scale:
            if n.velocity < key_velocity_thresh:
                removed['key'] += 1
                continue
        cleaned.append(n)

    total = sum(removed.values())
    if total > 0:
        print(f"    Filtered {total} ghost notes "
              f"(vel:{removed['velocity']} dur:{removed['duration']} key:{removed['key']})")
    return cleaned


def build_pattern_with_durations(notes, tempo, bars, resolution):
    """Build Strudel pattern with @duration notation for held notes."""
    if not notes:
        return None

    beat_dur = 60.0 / tempo
    step_dur = beat_dur * 4 / resolution
    total_steps = bars * resolution

    # Build events with start step and duration in steps
    events = []
    for n in notes:
        start = int(round(n.start / step_dur)) % total_steps
        end = int(round(n.end / step_dur)) % total_steps
        if end <= start:
            end = start + 1
        dur = min(end - start, total_steps - start)
        dur = max(1, dur)
        events.append({
            'step': start,
            'dur': dur,
            'name': note_name(n.pitch),
            'vel': n.velocity,
        })

    # Group simultaneous events by step
    step_events = {}
    for e in events:
        step_events.setdefault(e['step'], []).append(e)

    # Walk through steps, building the pattern
    parts = []
    step = 0
    while step < total_steps:
        if step in step_events:
            evts = step_events[step]
            # Use the longest duration among simultaneous notes
            max_dur = max(e['dur'] for e in evts)
            names = list(dict.fromkeys(e['name'] for e in evts))

            if len(names) == 1:
                token = names[0]
            else:
                token = f"[{','.join(names)}]"

            if max_dur > 1:
                token += f"@{max_dur}"

            parts.append(token)
            step += max_dur
        else:
            # Rest - count consecutive empty steps
            rest_len = 0
            while step + rest_len < total_steps and (step + rest_len) not in step_events:
                rest_len += 1
            if rest_len > 1:
                parts.append(f"~@{rest_len}")
            else:
                parts.append('~')
            step += rest_len

    # Remove trailing rests
    while parts and parts[-1].startswith('~'):
        parts.pop()
    if not parts:
        return None

    return ' '.join(parts)


def midi_to_strudel(midi, tempo, bars, resolution, analysis, min_velocity, min_duration):
    key_str = analysis.get('key') if analysis else None
    key_scale = SCALE_DEGREES.get(key_str)
    if key_scale:
        print(f"  Key filter active: {key_str}")

    tracks = []
    for i, inst in enumerate(midi.instruments):
        if not inst.notes:
            continue

        name = inst.name.strip() if inst.name and inst.name.strip() else f"track_{i}"
        print(f"  Track: {name} ({len(inst.notes)} notes)")

        cleaned = clean_notes(inst.notes, min_velocity, min_duration, key_scale)
        if not cleaned:
            print(f"    Skipped (no notes after cleaning)")
            continue

        pattern = build_pattern_with_durations(cleaned, tempo, bars, resolution)
        if not pattern:
            continue

        sound = strudel_sound(inst.program, inst.is_drum)

        # Calculate average velocity for gain
        avg_vel = sum(n.velocity for n in cleaned) / len(cleaned)
        gain = round(avg_vel / 100, 2)

        line = f'  // {name} ({len(cleaned)} notes)\n'
        line += f'  note("{pattern}")\n'
        line += f'    .s("{sound}").gain({gain})'

        if sound in ('sawtooth', 'square', 'triangle'):
            line += '.cutoff(1200).decay(0.4).sustain(0.5)'
        if sound == 'bass':
            line += '.cutoff(400)'

        tracks.append(line)

    if not tracks:
        return '// No patterns extracted\nnote("c3 e3 g3 c4").s("piano")'

    cps = round(tempo / 60 / 4, 4)

    code = f'// Generated from MIDI\n'
    if analysis:
        code += f'// Analysis: {analysis.get("key", "?")} | {round(tempo)} BPM'
        if 'unique_chords' in analysis:
            code += f' | Chords: {", ".join(analysis["unique_chords"][:8])}'
        code += '\n'
    code += f'// Bars: {bars} | Resolution: 1/{resolution}\n\n'
    code += f'setcps({cps})\n\n'

    if len(tracks) == 1:
        code += tracks[0].strip()
    else:
        code += 'stack(\n'
        code += ',\n'.join(tracks)
        code += '\n)'

    return code


def main():
    parser = argparse.ArgumentParser(description='MIDI/MusicXML to Strudel with analysis-aware cleaning')
    parser.add_argument('input', help='Input MIDI (.mid) or MusicXML (.musicxml) file')
    parser.add_argument('-o', '--output', help='Output .strudel.js file')
    parser.add_argument('--analysis', '-a', help='Analysis JSON from audio-to-midi (auto-detected if omitted)')
    parser.add_argument('--bars', type=int, default=4, help='Pattern length in bars (default: 4)')
    parser.add_argument('--resolution', type=int, default=16, choices=[4, 8, 16, 32],
                        help='Grid: 4/8/16/32 (default: 16)')
    parser.add_argument('--min-velocity', type=int, default=40,
                        help='Min note velocity 0-127 to keep (default: 40)')
    parser.add_argument('--min-duration', type=float, default=0.05,
                        help='Min note duration in seconds (default: 0.05)')
    parser.add_argument('--no-key-filter', action='store_true',
                        help='Disable key-based ghost note filtering')
    parser.add_argument('--tempo', type=float, help='Override tempo BPM (default: from analysis or MIDI)')
    parser.add_argument('--open', action='store_true', help='Open in strudel.cc in browser')
    args = parser.parse_args()

    ensure_deps()

    src = Path(args.input).resolve()
    if not src.exists():
        print(f"Error: not found: {src}", file=sys.stderr)
        sys.exit(1)

    # Load analysis
    analysis_path = args.analysis or find_analysis(src)
    analysis = None
    if analysis_path:
        analysis = load_analysis(analysis_path)
        if analysis:
            print(f"  Analysis loaded: {analysis_path}")

    # Determine tempo
    midi = load_input(src)
    if args.tempo:
        tempo = args.tempo
    elif analysis and 'tempo_bpm' in analysis:
        tempo = analysis['tempo_bpm']
    else:
        tempo = midi.estimate_tempo()
    print(f"  Tempo: {round(tempo)} BPM")

    if args.no_key_filter and analysis:
        analysis.pop('key', None)

    code = midi_to_strudel(midi, tempo, args.bars, args.resolution,
                           analysis, args.min_velocity, args.min_duration)

    out_path = Path(args.output).resolve() if args.output else src.with_suffix('.strudel.js')
    out_path.write_text(code, encoding='utf-8')
    print(f"\n  Strudel code: {out_path}")

    if args.open:
        import webbrowser
        webbrowser.open("https://strudel.cc/#" + quote(code))
        print("  Opened in browser!")
    else:
        print(f"  Paste into https://strudel.cc/ to play & tweak.\n")

    print(f"{'=' * 60}")
    print(code)
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
