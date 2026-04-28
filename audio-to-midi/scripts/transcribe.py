#!/usr/bin/env python3
"""Audio-to-MIDI/MusicXML transcription with full music analysis."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SUPPORTED_FORMATS = ('.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma')


def ensure_deps(packages):
    missing = []
    for module, pip_name in packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(pip_name)
    if missing:
        print(f"Installing: {', '.join(missing)}")
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', '--quiet'] + missing,
            stdout=subprocess.DEVNULL
        )


def ensure_core():
    ensure_deps({
        'basic_pitch': 'basic-pitch',
        'librosa': 'librosa',
        'music21': 'music21',
        'pretty_midi': 'pretty_midi',
        'numpy': 'numpy',
    })


def ensure_demucs():
    ensure_deps({'demucs': 'demucs'})


def ensure_piano_model():
    ensure_deps({
        'piano_transcription_inference': 'piano_transcription_inference',
        'torch': 'torch',
    })
    import os, urllib.request
    dest_dir = os.path.expanduser('~/piano_transcription_inference_data')
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, 'note_F1=0.9677_pedal_F1=0.9186.pth')
    if not os.path.exists(dest):
        url = 'https://zenodo.org/record/4034264/files/CRNN_note_F1%3D0.9677_pedal_F1%3D0.9186.pth?download=1'
        print("  Downloading piano model (~165MB)...")
        urllib.request.urlretrieve(url, dest)
    return dest


def _get_model_path():
    """Resolve the best available model file (ONNX > TFLite > SavedModel)."""
    from basic_pitch import ICASSP_2022_MODEL_PATH
    base = str(ICASSP_2022_MODEL_PATH)
    for suffix in ('.onnx', '.tflite', ''):
        p = Path(base + suffix)
        if p.exists():
            return p
    return Path(base)


def transcribe_basic_pitch(audio_path, output_dir, onset_thresh=0.5, frame_thresh=0.3,
                           min_note_ms=58, min_freq=None, max_freq=None):
    from basic_pitch.inference import predict

    model_path = _get_model_path()
    print(f"  Transcribing with Basic Pitch ({model_path.suffix or 'saved_model'})...")
    model_output, midi_data, note_events = predict(
        str(audio_path),
        model_or_model_path=model_path,
        onset_threshold=onset_thresh,
        frame_threshold=frame_thresh,
        minimum_note_length=min_note_ms,
        minimum_frequency=min_freq,
        maximum_frequency=max_freq,
    )

    midi_path = output_dir / f"{Path(audio_path).stem}.mid"
    midi_data.write(str(midi_path))
    print(f"  MIDI: {midi_path}")
    return midi_path, note_events


def transcribe_piano(audio_path, output_dir):
    """High-accuracy piano transcription using ByteDance's CRNN model."""
    import librosa
    from piano_transcription_inference import PianoTranscription

    print("  Transcribing with Piano Model (ByteDance CRNN)...")
    sr = 16000
    audio, _ = librosa.load(str(audio_path), sr=sr, mono=True)
    print(f"  Audio: {len(audio)/sr:.1f}s")

    transcriptor = PianoTranscription(device='cpu', checkpoint_path=None)
    midi_path = output_dir / f"{Path(audio_path).stem}.mid"
    transcriptor.transcribe(audio, str(midi_path))
    print(f"  MIDI: {midi_path}")
    return midi_path


def transcribe(audio_path, output_dir, engine='basic-pitch', onset_thresh=0.5,
               frame_thresh=0.3, min_note_ms=58, min_freq=None, max_freq=None):
    if engine == 'piano':
        return transcribe_piano(audio_path, output_dir), None
    else:
        return transcribe_basic_pitch(audio_path, output_dir, onset_thresh, frame_thresh,
                                      min_note_ms, min_freq, max_freq)


def to_musicxml(midi_path, output_dir):
    from music21 import converter

    print(f"  Converting to MusicXML...")
    score = converter.parse(str(midi_path))
    xml_path = output_dir / f"{midi_path.stem}.musicxml"
    score.write('musicxml', fp=str(xml_path))
    print(f"  MusicXML: {xml_path}")
    return xml_path


def separate_stems(audio_path, output_dir):
    ensure_demucs()

    print("  Separating stems with Demucs (htdemucs)...")
    stems_root = output_dir / "stems"
    subprocess.run(
        [sys.executable, '-m', 'demucs', '-n', 'htdemucs', '-o', str(stems_root), str(audio_path)],
        check=True,
    )

    stem_dir = stems_root / "htdemucs" / Path(audio_path).stem
    found = {}
    for name in ('vocals', 'drums', 'bass', 'other'):
        p = stem_dir / f"{name}.wav"
        if p.exists():
            found[name] = p
            print(f"    Stem: {name}")
    return found


def detect_key(chroma_avg):
    import numpy as np

    major = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    minor = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    best_corr, best_key, best_mode = -1, 'C', 'major'
    for i in range(12):
        rotated = np.roll(chroma_avg, -i)
        for profile, mode in [(major, 'major'), (minor, 'minor')]:
            corr = float(np.corrcoef(rotated, profile)[0, 1])
            if corr > best_corr:
                best_corr, best_key, best_mode = corr, notes[i], mode

    return best_key, best_mode, round(best_corr, 3)


def detect_chords(chroma, sr, hop_length=512):
    import numpy as np

    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    maj_template = [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]
    min_template = [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0]

    n_segments = max(1, min(64, chroma.shape[1] // 8))
    seg_len = chroma.shape[1] // n_segments
    chords = []

    for s in range(n_segments):
        seg_chroma = np.mean(chroma[:, s * seg_len:(s + 1) * seg_len], axis=1)
        time_sec = round(s * seg_len * hop_length / sr, 2)

        best_corr, best_chord = -1, 'C'
        for i in range(12):
            for template, suffix in [(maj_template, ''), (min_template, 'm')]:
                corr = float(np.corrcoef(seg_chroma, np.roll(template, i))[0, 1])
                if corr > best_corr:
                    best_corr = corr
                    best_chord = notes[i] + suffix

        if not chords or chords[-1]['chord'] != best_chord:
            chords.append({'time': time_sec, 'chord': best_chord})

    return chords


def analyze(audio_path):
    import librosa
    import numpy as np

    print(f"\n  Analyzing audio...")
    y, sr = librosa.load(str(audio_path))
    duration = round(len(y) / sr, 2)

    # Tempo
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0])
    tempo = round(tempo, 1)
    print(f"    Tempo: {tempo} BPM")

    # Key
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_avg = np.mean(chroma, axis=1)
    key_name, key_mode, key_conf = detect_key(chroma_avg)
    print(f"    Key: {key_name} {key_mode} (confidence: {key_conf})")

    # Chords
    chords = detect_chords(chroma, sr)
    unique = list(dict.fromkeys(c['chord'] for c in chords))
    print(f"    Chords: {', '.join(unique[:16])}{'...' if len(unique) > 16 else ''}")

    # Dynamics
    rms = librosa.feature.rms(y=y)[0]
    eps = 1e-10
    dynamics = {
        'mean_db': round(float(20 * np.log10(np.mean(rms) + eps)), 1),
        'max_db': round(float(20 * np.log10(np.max(rms) + eps)), 1),
        'min_db': round(float(20 * np.log10(np.min(rms[rms > eps]) + eps)), 1) if np.any(rms > eps) else -80.0,
        'dynamic_range_db': round(float(20 * np.log10((np.max(rms) + eps) / (np.min(rms[rms > eps]) + eps))), 1) if np.any(rms > eps) else 0.0,
    }
    print(f"    Dynamics: mean={dynamics['mean_db']}dB, range={dynamics['dynamic_range_db']}dB")

    # Spectral / instrument hints
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))
    rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))

    instruments = []
    if centroid < 500:
        instruments.append('bass-heavy')
    if 500 <= centroid < 2000:
        instruments.append('mid-range (guitar/keys/vocals)')
    if centroid >= 2000:
        instruments.append('high-range (synth/cymbals)')
    if zcr > 0.1:
        instruments.append('percussive elements')

    spectral = {
        'centroid_hz': round(centroid, 1),
        'bandwidth_hz': round(bandwidth, 1),
        'rolloff_hz': round(rolloff, 1),
        'zero_crossing_rate': round(zcr, 4),
    }
    print(f"    Instruments: {', '.join(instruments)}")

    return {
        'duration_seconds': duration,
        'tempo_bpm': tempo,
        'key': f"{key_name} {key_mode}",
        'key_confidence': key_conf,
        'chords': chords,
        'unique_chords': unique,
        'dynamics': dynamics,
        'spectral': spectral,
        'instrument_hints': instruments,
    }


def main():
    parser = argparse.ArgumentParser(description='Audio to MIDI/MusicXML transcription with analysis')
    parser.add_argument('input', help='Input audio file (MP3, WAV, FLAC, OGG, M4A)')
    parser.add_argument('-o', '--output', help='Output directory (default: same as input file)')
    parser.add_argument('--engine', choices=['basic-pitch', 'piano'], default='basic-pitch',
                        help='Transcription engine: basic-pitch (general) or piano (high-accuracy piano)')
    parser.add_argument('--stems', action='store_true',
                        help='Separate into stems (vocals/drums/bass/other) with Demucs before transcription')
    parser.add_argument('--onset-threshold', type=float, default=0.5,
                        help='Basic Pitch onset sensitivity 0-1 (default: 0.5)')
    parser.add_argument('--frame-threshold', type=float, default=0.3,
                        help='Basic Pitch frame sensitivity 0-1 (default: 0.3)')
    parser.add_argument('--min-note-length', type=int, default=58,
                        help='Minimum note length in ms (default: 58)')
    parser.add_argument('--no-analysis', action='store_true', help='Skip audio analysis')
    parser.add_argument('--no-musicxml', action='store_true', help='Skip MusicXML output')
    args = parser.parse_args()

    src = Path(args.input).resolve()
    if not src.exists():
        print(f"Error: not found: {src}", file=sys.stderr)
        sys.exit(1)
    if src.suffix.lower() not in SUPPORTED_FORMATS:
        print(f"Error: unsupported format {src.suffix}. Supported: {', '.join(SUPPORTED_FORMATS)}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.output).resolve() if args.output else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.engine == 'piano':
        ensure_piano_model()
        ensure_deps({'librosa': 'librosa', 'music21': 'music21', 'pretty_midi': 'pretty_midi', 'numpy': 'numpy'})
    else:
        ensure_core()

    print(f"\n{'=' * 60}")
    print(f"  Audio-to-MIDI Transcription")
    print(f"  Input:  {src}")
    print(f"  Output: {out_dir}")
    print(f"  Engine: {args.engine}")
    print(f"  Stems:  {'yes' if args.stems else 'no'}")
    print(f"{'=' * 60}\n")

    outputs = []

    if args.stems:
        stem_files = separate_stems(src, out_dir)
        for stem_name, stem_path in stem_files.items():
            print(f"\n--- Stem: {stem_name} ---")
            midi_path, _ = transcribe(stem_path, out_dir, args.engine,
                                      args.onset_threshold, args.frame_threshold, args.min_note_length)
            entry = {'stem': stem_name, 'midi': str(midi_path)}
            if not args.no_musicxml:
                xml_path = to_musicxml(midi_path, out_dir)
                entry['musicxml'] = str(xml_path)
            outputs.append(entry)
    else:
        midi_path, _ = transcribe(src, out_dir, args.engine,
                                  args.onset_threshold, args.frame_threshold, args.min_note_length)
        entry = {'midi': str(midi_path)}
        if not args.no_musicxml:
            xml_path = to_musicxml(midi_path, out_dir)
            entry['musicxml'] = str(xml_path)
        outputs.append(entry)

    analysis = None
    if not args.no_analysis:
        analysis = analyze(str(src))
        analysis_path = out_dir / f"{src.stem}_analysis.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"\n  Analysis JSON: {analysis_path}")

    print(f"\n{'=' * 60}")
    print("  Output files:")
    for o in outputs:
        tag = f"[{o['stem']}] " if 'stem' in o else ""
        print(f"    {tag}MIDI:     {o['midi']}")
        if 'musicxml' in o:
            print(f"    {tag}MusicXML: {o['musicxml']}")
    print(f"{'=' * 60}")

    return {'outputs': outputs, 'analysis': analysis}


if __name__ == '__main__':
    main()
