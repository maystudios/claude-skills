# Seedance 2.0 — Prompt Engineering Reference

Deep reference for authoring, directing, and debugging Seedance 2.0 prompts. Read this for any non-trivial single-shot prompt, camera direction, multi-shot storyboard, style work, or artifact debugging. Audio prompting is in `audio.md`; references/frames in `references-and-frames.md`.

## Contents
1. Prompt formula & ordering
2. Camera control vocabulary
3. Motion & physics
4. Cinematic & style language
5. Multi-shot / timeline prompting
6. Length, language, phrasing
7. Negative prompts
8. Common mistakes (anti-patterns)
9. Worked example prompts

---

## 1. Prompt formula & ordering

The most-repeated structure across community and official-derived guides:

```
[Subject] + [Action] + [Environment] + [Camera] + [Lighting] + [Style] + [Constraints]
```

A camera-first variant (`Camera → Subject → Action → Environment → Lighting → Style`) is equally valid when the shot is defined by its move. All variants share one principle: **the model reads left-to-right and weights the front most heavily.** The first 2–3 instructions get reliable adherence; after ~8 requirements, typically only 4–5 land. Front-load the subject and the single most important action.

Fill-in scaffold (labeled fields are fine — the model accepts `Subject:` / `Camera:` style tags too):

```
Subject:    [who/what, age, material, wardrobe]
Action:     [one clear verb, present tense]
Environment:[place, time of day, weather]
Camera:     [shot size] + [one movement] + [angle]
Lighting:   [named lighting setup]
Style:      [2–3 named anchors] + [color grade]
Constraints:[keep-fixed clause], [duration], [aspect ratio], [avoid: observed defect]
```

Guides consistently report that **short, structured prompts beat long poetic ones**. Aim for 60–100 words on a single shot.

---

## 2. Camera control vocabulary

The model responds to **directorial pacing language, not camera math.** Use "slow, smooth, gradual, gentle" — NOT "24fps, f/2.8, ISO 800, 85mm". Focal length is best expressed as feel ("wide 24mm feel", "telephoto 85mm+ compression"), not numbers.

**Shot sizes:** extreme wide / establishing, wide, medium, close-up, extreme close-up, over-the-shoulder (OTS). Pair wide shots with slow/locked moves; pair close-ups with tiny push-ins. Avoid fast pans on wide shots.

**Camera moves the model reliably follows:**

| Term | Effect |
|------|--------|
| Push-in / dolly-in | moves toward subject |
| Pull-back / dolly-out | moves away, reveals wider frame |
| Pan (left/right) | horizontal rotation |
| Tilt (up/down) | vertical rotation |
| Tracking / follow | camera follows the subject laterally or from behind |
| Orbit / arc | circles the subject (partial or 360°) |
| Crane / jib | vertical rise or descent |
| Aerial / drone | high-altitude, bird's-eye |
| Steadicam / gimbal | smooth stabilized glide |
| Handheld | natural slight shake / micro-jitter |
| Fixed / static / locked-off | camera completely still |
| Rack focus | focus shift between foreground/background |

**High-risk moves (use sparingly, often degrade quality):** whip pan, snap zoom, Dutch angle, and any fast/stylized move.

**Angles:** low-angle, high-angle, eye-level, bird's-eye, Dutch (tilted).

**POV / first-person** is a distinct, supported mode — but you must state what the camera is *not* doing: "one continuous shot, first-person POV, no cuts, no zoom, natural head movement". Without that lock, the model defaults to cutting between angles and the POV illusion breaks.

**The three camera rules that matter most:**
1. **One primary camera instruction per shot.** Stacking moves ("pan + zoom + dolly + handheld") produces incoherent footage.
2. **Describe rhythm, not specs.** Pacing words over camera numbers.
3. **Separate camera movement from subject movement** into different sentences. ✅ "The dancer spins slowly. The camera holds a fixed frame." ❌ "spinning camera around a dancing person."

---

## 3. Motion & physics

Seedance was trained on physical interactions — **it understands physics, not adjectives.** "Tires smoke as the car pivots 90° on wet asphalt" outperforms "car turns dramatically" because the model can simulate weight, friction, and impact but cannot render the *word* "dramatic".

**One primary action per shot / per beat.** Compound choreography causes "melting" and limb distortion.

**Speed / pacing tiers** (the bare word "fast", unqualified, is the single most-cited quality-killer — always qualify pace):
- Imperceptible: "barely moving, almost still"
- Slow (recommended default): "slow, gentle, gradual, smooth"
- Medium: "controlled, steady, natural pace"
- Fast (highest-risk): "dynamic, swift, rapid" — apply to ONE element only, never the whole scene

**Physics language that lands:** "realistic weight and inertia", "landing cushioning", "impact shows visible shockwave ripples", cloth/fabric sway, wet-fabric cling, fluid dynamics, dust/debris kicked up by force.

**Anti-floating / anti-deformation guardrails** to append when limbs or gait go wrong: "feet touching the ground, no floating", "natural gait", "normal human structure, natural proportions".

For precise timing/gesture rhythm, a **reference video** (`@Video1` — see `references-and-frames.md`) is more reliable than text alone.

---

## 4. Cinematic & style language

**Lighting is the single highest-leverage element.** If you can only add one thing to a prompt to improve quality, add a lighting description.
Vocabulary: golden hour, rim light / hard rim light, natural window light, backlit / silhouette, neon, overcast / diffused, volumetric light / god rays, low-key, motivated lighting from a practical source, single focused spotlight with sharp falloff.

**Lens / film-look terms:** 35mm film grain, anamorphic lens flare, shallow depth of field, rack focus, long-lens compression, halation on highlights, soft highlight rolloff.

**Color grading:** teal-and-orange, bleach bypass / desaturated / gritty, warm shadows with cool highlights, high-contrast monochrome, "90s Hong Kong" yellow-green tint.

**Named style anchors beat vague adjectives** — this is load-bearing. Replace "beautiful/cinematic/epic/amazing" with a concrete reference:
- "Wes Anderson symmetry" instead of "beautiful"
- "35mm film grain, Kodak color palette" instead of "cinematic"
- "Fincher-level precision" instead of "amazing"
- Genre anchors: "Tsui Hark-style wuxia", "neon-noir high contrast", "naturalistic film-print emulation", "100% real-life shooting texture"

Stack **2–3 style anchors max** — more creates visual noise and dilutes adherence.

**Optional quality suffix** to append when outputs look soft/unstable:
> "rich details, sharp clarity, natural colors, stable picture, no blur, no ghosting, no flickering"

Without any explicit style line, the model falls back to its own default aesthetic — always end with a style anchor.

---

## 5. Multi-shot / timeline prompting

Seedance 2.0 can generate **multiple shots in a single call** (a headline 2.0 feature). Two syntaxes work:

**(a) Numbered scenes** — describe discrete shots with individual actions:
> "A lonely robot wakes in an abandoned factory (Scene 1). It walks outside to a sunset wasteland (Scene 2). It finds a small flower and gently touches it (Scene 3). It looks up and smiles at the sky (Scene 4). Keep robot appearance consistent. Warm tones, no flicker."

**(b) Bracketed timeline** — state shot count / duration / ratio up front, then timecoded beats:
```
Total: 15s / 6 shots / 16:9
[0s] Wide shot: neon alley, rain. Camera static.
[3s] Slow dolly forward begins.
[6s] Now medium shot on the figure. Camera continues push-in.
[8s] Rack focus: background sharpens, then returns to subject.
...
```

**Beat count by duration** (don't cram six events into five seconds):
- 4–5s → 2–3 beats
- 7s → 3–4 beats
- 10s → 4 beats (e.g. [0s],[3s],[6s],[8s])
- 15s → 5–6 beats / up to 6 shots

**Rule: one action + one camera instruction per beat.** Overstuffing a single timestamp is the #1 timeline mistake.

**Narrative arc** convention: calm → trigger → transformation/climax → resolution.

**Transitions must be explicit** or the model cuts jarringly: "Cut to:", "Dissolve into", "Rack focus from background to subject", "Hold."

**Consistency lock:** restate identity in every beat or add a lock clause — "Maintain consistent facial features and clothing throughout the entire video." Frame it positively (what stays fixed) rather than as a negative.

**Chaining beyond 15s:** generate clip 1 → feed its output back as `@Video1` → "Continue from @Video1. [new scene]. Maintain the exact same lighting/character/style." Consistency holds well for ~3–6 chained extensions (30–90s); beyond that, re-anchor with the original reference image. (See also the `video-extend` endpoint in `references-and-frames.md`.)

---

## 6. Length, language, phrasing

- **Length:** 60–100 words is the single-shot sweet spot; 50–150 acceptable. Hard technical ceiling ~3000 characters, but the model starts averaging/ignoring instructions past ~150 words semantically. Multi-shot/timeline prompts legitimately run longer (100–300+ words).
- **Natural language over keyword stacking.** Prompts should read like directorial notes, not adjective lists.
- **English vs. Chinese:** the model natively understands both. English is more stable overall, especially for camera and style directives. A reported power-user technique: use Chinese for emotional/scene description and English for camera/style terms in the same prompt. (Chinese support is improving; treat the mixing tip as a community heuristic, not a guarantee.)
- **Structured/tagged prompts** (`Subject:` / `Action:` / `Camera:` / `Style:` / `Constraints:`) are a fine scaffold and often improve adherence.

---

## 7. Negative prompts

**There is no reliable dedicated `negative_prompt` field at the raw API level** (documented request bodies expose `resolution`/`ratio`/`duration`/`seed`/`watermark`/`generate_audio`/`return_last_frame`). Some UIs/wrappers expose a "negative prompt" box that just gets appended to the main prompt. Sources genuinely disagree on whether negatives help — treat them as an *inline avoid-clause*, not a separate mechanism.

**Practical consensus (works regardless of mechanism):**
- Keep negatives **short and targeted to an actually-observed defect** (2–3 terms). Long generic blocklists dull the image.
- Prefer **positive framing**: "stable face, normal human structure" over "no distortion".
- Standard character boilerplate: **"avoid jitter and bent limbs"**. Situational: "avoid temporal flicker" (long clips), "avoid identity drift" (multi-shot), "avoid chaotic composition" (busy scenes).

---

## 8. Common mistakes (anti-patterns)

1. **Stacking camera moves** in one instruction → jitter. One primary move only.
2. **Mixing camera + subject motion** in one clause → uncontrollable footage. Split into two sentences.
3. **Bare "fast" / "lots of movement"** → the top quality-killer. Qualify pace; speed one element only.
4. **Vague adjectives** ("cinematic/epic/amazing/beautiful/masterpiece") → the model has nothing to render. Use named anchors.
5. **Photography jargon** (fps, f-stops, ISO, ARRI/RED, focal-length numbers) → weak response. Use rhythm words.
6. **Over-length single-shot prompts (>150 words)** → the model averages and drops instructions.
7. **Multiple complex simultaneous actions** → "melting"/distortion. One action per shot/beat.
8. **No consistency lock** in multi-shot/reference prompts → character & outfit drift.
9. **Vague/unlabeled `@` references** → unpredictable blending. State what each reference controls.
10. **Content/duration mismatch** → six events in a 5s clip. Scale beats to runtime.
11. **Omitting the style line** → the model falls back to its own default look.
12. **Expecting clean in-video text** → renders poorly; add text/captions in post.
13. **Stacking too many negatives** → dulls the image. Keep to 2–3 targeted terms.

---

## 9. Worked example prompts

All verbatim from published guides; use as structural templates.

**Single-shot action (physics-forward):**
> "A short-haired female agent in tactical winter gear engages in close-quarters combat with a mercenary at a snowy military base. The mercenary throws a punch; she dodges swiftly and counters with a powerful elbow strike to his face mask, followed by a heavy knee to the stomach. Impact shows visible shockwave ripples, and sweat and saliva fly through the air as the enemy's body folds from the blow. The camera follows the action with dynamic handheld movement."

**Quiet character moment (single continuous shot, ambient-only audio):**
> "Single continuous shot. A young woman in an oversized hoodie pushes open a convenience store door. Rain streaks the glass behind her. Warm fluorescent light floods over her face. She walks slowly down the snack aisle, trailing one finger along the shelves. She stops, picks up a cup of instant noodles, reads the label, puts it back. She stands still for a moment. Camera holds on her face — neutral expression, eyes slightly distant. She grabs the noodles again and walks to the counter. Wide shot from outside the glass as she pays, rain blurring the frame. No music. Only ambient store sounds and rain."

**Luxury product 360° (commercial, locked macro):**
> "A minimalist black matte mechanical keyboard on a pure white infinite studio background, rotating smoothly 360 degrees clockwise. RGB lighting gently breathing. Keycap text sharp and readable. Fixed macro camera, smooth turntable motion, commercial product photography style, soft high-key lighting, no noise. Logo and text remain perfectly consistent."

**Multi-shot narrative arc (4 beats, single generation):**
> "A lonely robot wakes up in an abandoned factory (Scene 1). It walks outside and sees a sunset wasteland (Scene 2). It discovers a small flower and gently touches it (Scene 3). Finally, it looks up and smiles at the sky (Scene 4). Keep robot appearance consistent. Emotional transition from confusion to warmth. Cinematic camera, warm tones, no flicker."

**Wuxia fight (reference-video-driven — see references-and-frames.md):**
> "A wuxia-style male hero (based on reference video character), wearing black martial outfit, fighting enemies in a rainy bamboo forest at night. Fast sword combos with visible sword light trails and splashing water. Fast follow camera, crane shots, and quick close-ups. Cinematic camera language. Maintain character appearance and clothing consistency. Realistic physics, wet fabric, rain interaction."

**Skateboard trick (compact single shot with constraints):**
> "A skateboarder lands a clean trick in an empty dawn parking lot, camera low tracking shot then subtle rise, modern cinematic contrast, 6 seconds, 16:9, avoid jitter and bent limbs."

**Establishing sci-fi (compact):**
> "A lone astronaut walks across an amber desert under twin moons, camera slow lateral tracking, cinematic sci-fi tone, 8 seconds, 16:9, avoid temporal flicker."

**Continuous push-in with OTS ending (dialogue-free, no music):**
> "Single continuous cinematic shot, no music. From outside the glass window, the dim camera slowly pushes inward into a pizza shop. A bearded male employee is baking pizza. He removes the pizza from the oven with a metal tray, places it into a red takeaway box, closes the lid, and hands it to a customer with a warm smile. Final shot: over-the-shoulder perspective."

**ASMR macro (sensory / audio-forward — see audio.md):**
> "Create a vertical ASMR video with no music, focusing on macro details. A light blue skincare gel bottle sits on glass. A pale, elegant hand gently taps the glass, producing crisp fingernail tapping sounds. The hand picks up the bottle and slowly twists the cap, with the rotation sound clearly audible. A spoon scoops a portion of gel and drops it onto the glass with a soft 'plop,' showing dense gel with tiny air bubbles."

**Short POV (demonstrates that terse prompts can work):**
> "A single-frame POV video of a medieval knight riding a horse with a sledgehammer in his hands, riding and fighting epically, smashing his opponents while riding, realistic, no cuts, natural head movement."
