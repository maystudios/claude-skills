# Seedance 2.0 — Native Audio

Seedance 2.0 generates **audio and video jointly in one pass** (dual-channel stereo), not as a post overlay. It produces dialogue with lip-sync, sound effects/foley, ambient sound, and music/score. This is the headline 2.0 upgrade. All audio is steered through the **prose prompt** — there are no volume/mix parameters and no separate stem exports (output is a single muxed MP4 track).

## Contents
1. The audio toggle & cost
2. Dialogue & lip-sync
3. Sound effects
4. Ambient & music (and suppressing unwanted music)
5. Mix priority
6. Reference audio / voice cloning (`@Audio`)
7. Languages
8. Limitations
9. Example prompts

---

## 1. The audio toggle & cost

- `generate_audio` — boolean, **default `true`**. Set `false` for a silent clip.
- **No price difference** whether audio is on or off (unlike Veo 3.1, where disabling audio halves the cost). Reasons to disable: you'll dub external TTS/voice actors, layer licensed music, or A/B-test voices against one visual take.
- Reference-audio input is a separate feature (§6) from the on/off toggle.

---

## 2. Dialogue & lip-sync

**Syntax:** wrap spoken lines in **double quotes** inside the natural-language prompt.
> `The man stopped and said: "Remember this moment."`

**Keep lines short** — lip-sync drifts on long lines. Rule of thumb: **~12 words per 10s clip, ~20 words per 15s clip.** For multi-sentence dialogue, insert written beats between sentences as resync anchors.

**Direct the delivery** after the line: `"...", delivered dry and a little proud`, or `quiet, intimate, slightly breathless, close-mic tone`.

**Tag the language** explicitly when non-English: `Character speaks in Japanese: "今日は天気がいいですね。"`

**Lip-sync is inherent** (no dedicated "lip-sync mode") whenever quoted dialogue is present, or when a reference audio/portrait is supplied (§6). Best conditions for reliable sync:
- Medium close-up with a **locked/fixed camera**
- Front-facing or slight three-quarter angle (profile shots are unreliable)
- High-resolution, well-lit, unobstructed face
- **Don't combine head-turn/nod camera direction with a dialogue line** — head motion competes with lip-sync and produces "half-motions"

Realistic expectation: good enough for shorts/social clips; single-character short lines are where it performs best. It optimizes for *sync precision*, not voice fidelity — dedicated TTS (e.g. ElevenLabs) has a higher voice-quality ceiling, at the cost of re-introducing sync drift when overdubbed.

---

## 3. Sound effects

Name the **source and material** concretely — "boots on wet cobblestone" ≠ "sneakers on hardwood". Anchor timing with timestamps when it matters:
> `SFX: thunder crack at 3s. Lightning illuminates the scene at the thunder crack.`

The model captures fine foley nuance (fabric rustle, tapping on glass/acrylic, bubble-wrap pops) when you describe it specifically.

---

## 4. Ambient & music (and suppressing unwanted music)

Treat the prompt like a **sound brief**:
> `Audio: the grind, the hiss of steam, a low acoustic guitar, no voiceover.`

For music, **mood/genre words beat technical music terms** ("lo-fi ambient piano", "tense orchestral build" > key signatures/BPM math, though loose BPM hints work).

**Suppress unwanted score:** open/vague prompts tend to come back scored like a car advert. Write the **literal phrase `no music`** (not "no background music"). For a fully silent clip via prompt (in addition to, or instead of, `generate_audio:false`):
> `silent, no dialogue, no ambient, no audio of any kind.`

---

## 5. Mix priority

There is no numeric mix control — state the hierarchy in words:
> `Dialogue clean and prominent, music low, ambient subtle.`

Keep to **2–3 simultaneous audio layers**; beyond three, the mix turns muddy.

---

## 6. Reference audio / voice cloning (`@Audio`)

Attach up to **3 audio clips** (`audio_url` single / `audio_urls` array; MP3/WAV, ≤15s combined, ≤15 MB each) and reference them in-prompt as `@Audio1`, `@Audio2`, `@Audio3` to drive voice timbre, rhythm, or lip-sync target. **Audio input must be accompanied by at least one image or video** (no audio-only conditioning).

This enables voice "cloning" from a supplied track and up to **3 distinct character voices per scene** (3 is the audio-input ceiling). It supports cross-gender adaptation (e.g. a male reference voice adapted to a female character). Lip-sync pattern:
> `@Image1 speaks directly to the camera while saying @Audio1.`

(One report says only MP3 uploads reliably while WAV may fail silently — prefer MP3 if a reference-audio upload misbehaves.)

---

## 7. Languages

Roughly **8+ spoken languages** with lip-synced dialogue, commonly: **English, Mandarin Chinese, Japanese, Korean, Spanish, Indonesian**, plus regional Chinese dialects/accents (Sichuanese, Cantonese) and singing/opera.
- Practical quality ranking: **Mandarin** most consistent lip-sync, **English** a close second; Japanese/Korean work but drift on longer phrases; non-English lip-sync is generally weaker.
- **Accent** is prompt-controlled ("American accent, conversational tone"), not a discrete parameter, and can drift between separate generations — re-specify it in every prompt.
- Languages beyond the ~6–8 commonly cited (e.g. French, German, Arabic, Hindi) are not confirmed in any source — don't promise them.

---

## 8. Limitations

- ByteDance acknowledges occasional **audio distortion**.
- **Multi-speaker lip-sync** is an open problem — single-character, short lines perform best.
- **Sync drift** grows with clip length and multi-sentence dialogue (mitigate with the word-count caps in §2).
- **Voice timbre isn't locked across separate generations** — a character's voice/accent can drift shot-to-shot.
- **Music/singing** is the weakest layer: BGM is "limited", structured songs/harmony and lyric singing are unreliable, humming is unpredictable.
- **No post-hoc mixing/EQ/stems** — one muxed track; to edit layers independently, generate dialogue-only and ambient-only passes separately and combine in an external editor.

---

## 9. Example prompts

**UGC ad with dialogue + explicit no-music cue:**
> "UGC creator, energetic man in his twenties standing in a concrete skatepark at golden hour, holding a new pair of white and neon-green sneakers. He lifts them close to the lens, rotates them slowly saying: 'Bro look at these. Feel that material.' He drops them, slides his foot in, stomps twice, jogs three steps and stops, turns back to camera: 'Insane comfort.' Filmed on iPhone, warm sunset backlight, slight lens flare, handheld. No music, no on-screen text."

**Two-line exchange with delivery direction:**
> Woman: "You always arrive just on time — do you enjoy cutting it close?" Man, quiet and worn out: "I have my own rhythm."

**Nature ambient, music-free:**
> "Audio carries the scene: heavy droplets hitting leaves, a far-off bird, the faint creak of branches, no music at all."

**Timed SFX anchor:**
> "SFX: thunder crack at 3s. Lightning illuminates the scene at the thunder crack."

**Reference-audio lip-sync (portrait + voice track):**
> "@Image1 speaks directly to the camera, natural expression, while saying @Audio1. Medium close-up, locked camera, soft window light."
