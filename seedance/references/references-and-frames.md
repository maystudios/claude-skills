# Seedance 2.0 — References, Start Frames & Consistency

How to condition Seedance 2.0 on images, videos, and prior clips: reference-to-video, start frames, first-and-last-frame interpolation, character consistency, style transfer, and clip continuation. Prompt-craft is in `prompting.md`; audio references in `audio.md`.

## Contents
1. The three image modes (mutually exclusive)
2. The `@` tagging convention
3. Reference counts, file specs & the 12-file cap
4. Start frame (image-to-video)
5. First-and-last frame
6. Keyframes & scene cuts (there is no >2-frame timeline)
7. Character / subject consistency
8. Style transfer
9. Real human faces & the asset library
10. Clip continuation / extending past 15s
11. Example workflows

---

## 1. The three image modes (mutually exclusive)

At the raw ByteDance/Volcengine/BytePlus (ModelArk) API level, images carry a `role`, and the following three scenarios **cannot be combined** in one call:

| Mode | Images | Roles |
|------|--------|-------|
| **First-frame only** (image-to-video) | 1 | `first_frame` |
| **First + last frame** | 2 | `first_frame`, `last_frame` |
| **Multimodal reference** (reference-to-video, **2.0 only**) | 1–9 | all `reference_image` |

Multimodal reference mode is where videos (`reference_video`, ≤3) and audio (`reference_audio`, ≤3) can also be attached. First/last-frame mode cannot also take references — to fake "first frame + references", stay in reference mode and designate the opening frame via the prompt ("use @Image1 as the opening frame").

> Host wrappers simplify this. **fal.ai** exposes separate endpoints — `.../seedance-2.0/text-to-video`, `/image-to-video` (with an optional `end_image_url` for first→last), and `/reference-to-video`. **Runware** uses a `frameImages` array (1–2, first/last) that cannot be mixed with `referenceImages`. Same underlying rules, different packaging.

---

## 2. The `@` tagging convention

Reference assets are addressed inside the prose prompt as `@Image1`, `@Image2`, …, `@Video1`, `@Audio1` (numbered by input/array order). Replicate's docs use `[Image1]` bracket form; `@ImageN` is the more widely corroborated, likely-canonical token.

**The cardinal rule: always state what each reference controls** — identity, camera motion, style, object, or audio. The single biggest reference failure mode is an unattributed asset ("just reference @Video1"). Say the *aspect*:
- "reference `@Video1` for the camera movement only"
- "reference `@Video1`'s choreography / gesture rhythm"
- "fully replicate `@Video1`'s effects and transitions"

And anchor a referenced subject with a **descriptor + tag**, not the bare tag: "the woman in `@Image1` with dark curly hair and a red leather jacket".

Do **not** contradict a reference in text (e.g. asking for "fast motion" against a slow-motion `@Video1`) — it produces flickering.

---

## 3. Reference counts, file specs & the 12-file cap

Per one generation, in multimodal reference mode:
- **Up to 9 images** + **up to 3 videos** (≤15s combined, <50 MB) + **up to 3 audio clips** (≤15s combined, ≤15 MB each)
- **Hard cap: 12 files total** across all modalities (shared budget — heavy image use trades off against video/audio slots)
- Audio cannot be sent alone — at least one image or video must accompany it

**Image requirements (official):**

| Property | Value |
|----------|-------|
| Formats | JPEG, PNG, WebP, BMP, TIFF, GIF, HEIC, HEIF |
| Max size | < 30 MB per image |
| Aspect ratio | between 0.4 and 2.5 |
| Pixel dimensions | 300–6000 px on each side |
| Content | no direct real human faces (see §9) |

**Practical count sweet spot:** 3–5 core reference images (don't max out all 9 slots), 1–2 video references, at most 1 audio track — leave headroom rather than overcrowd.

**Weighting:** the API/`@`-tag system has **no numeric weight field**; influence is controlled by how prominently you describe a reference and its position (place the priority subject's tag early). (The Jimeng/Dreamina *consumer app* has per-image weight sliders, but that is a UI feature, not an API parameter.)

---

## 4. Start frame (image-to-video)

Supply one image + a prompt. The image defines the static content (subject, composition, lighting, color); **the prompt should describe motion, camera, and pacing — not restate what's already visible.**

- Weak: "A luxury perfume bottle on a table."
- Strong: "Slow dolly-in. The bottle catches a soft highlight as the camera moves."

fal.ai `image-to-video` parameters: `prompt` (required), `image_url` (required), `end_image_url` (optional), `resolution` (480p/720p, some tiers 1080p), `duration` (4–15 or `auto`), `aspect_ratio`, `generate_audio` (default true), `seed`.

**Good start-frame images:** sharp and clean (avoid compression noise), even/intentional lighting (it propagates through the whole clip), plain backgrounds (busy patterns flicker), and leave "motion space" — position the subject opposite the intended movement direction. Inspect AI-generated first frames for artifacts (malformed hands, asymmetry): such errors compound across every generated frame.

Note: the Seedance 1.x parameters `frames` and `camera_fixed` are **not supported** in 2.0 — use the integer `duration` instead.

---

## 5. First-and-last frame

Supply two images (`role: first_frame` and `role: last_frame`, or fal's `image_url` + `end_image_url`) plus a prompt. The model **generates new in-between frames** to plan a motion trajectory from start to end — reducing drift/flicker versus single-image animation. Best for controlled transitions: product reveals, before/after, logo outros, day→night.

**Requirements — stricter than single-frame:**
- **Matching resolution and aspect ratio** between the two frames (prepare both at the same size). If ratios differ, the first frame takes precedence and the last is auto-cropped.
- Similar subject scale/position, consistent lighting direction and color temperature, related subject matter. Large jumps (tight close-up → wide aerial) force the model to invent too much and invite warping.

**Prompt phrasing for transitions:** use continuity words — "smooth, continuous, gradual, seamless" — and name the element that must stay constant ("the same character", "keep the logo unchanged"). The last frame is a **directional target, not pixel-perfect**.

Example prompt:
> "Smooth continuous shot, the camera slowly pushes in while the closed package opens to reveal the product on the final frame. Soft studio lighting, clean reflections, natural physical motion, no abrupt cuts."

---

## 6. Keyframes & scene cuts (there is no >2-frame timeline)

Seedance 2.0 caps **positional anchor frames at two** (first + last). There is no documented N-keyframe timeline or per-timestamp frame injection.

To storyboard multiple beats, use one of:
- **Prompt-driven scene cuts** in reference mode: "`@Image1` finds a football in the ocean and picks it up excitedly. Cut scene to `@Image1` calling friends over. Cut scene to a group playing football underwater." (This is narrative sequencing, not frame-position keyframing.)
- **Multi-shot timeline prompting** — see `prompting.md` §5.
- **Chaining** via video-extend / `return_last_frame` — see §10.

("Beat-sync" in some guides means syncing cuts to an audio track's rhythm — a different sense of "keyframe".)

---

## 7. Character / subject consistency

Consistency is the main failure mode; it degrades across long clips and crowds (3+ characters blend/drift). Techniques, strongest first:

**Reference pack (per character):** 3 stills max — straight-on, three-quarter, profile — from the **same session and lighting**, same expression; optionally a 2–3s clip of a neutral head nod/blink as a motion anchor.
- **Avoid collages** (the model reads a multi-pose collage as one busy scene).
- **Avoid mixed lighting** across the stills (the model averages them into a flat, neutral look).
- Avoid all-headshot sets with no body/context, and blurry/watermarked images.

**In-prompt anchoring:** tie the character to its tag and **repeat that anchor across every shot/beat** ("the man from @Image1, walking tiredly through the corridor…"). Lock one or two *hard traits* (a mole, jacket texture, a logo) and pin age range and hair. Use phrases like "Keep facial proportions identical to the reference across all frames", "no new jewelry, no makeup or hair changes beyond natural sway". Avoid vague aesthetic words when identity matters.

**QA:** check first/mid/final frames for drift in eye distance and jaw angle; watch hand-to-face transitions; track micro-features (moles, logos) as early drift indicators.

**Cross-session identity:** for the *same* character across many separate generations, register it in the asset library (§9).

---

## 8. Style transfer

Style is a prompting pattern on the same `reference_image` mechanism — there is no separate "style mode".
- Dedicate one or a few images purely to palette/lighting/mood ("style swatches"), tagged and described **separately** from the identity image: "`@Image1` is the subject; match the color palette and lighting of `@Image2`."
- Or pull style from a **reference video** — it can transfer whole "creative templates": ad formats, VFX, film techniques, editing/transition style, camera choreography — decoupled from that video's actual subject.

Example (object + style + motion transfer):
> "Apply the 360-degree rotation path of `@Video1` to the product shown in `@Image1`. Background: a clean marble surface with soft shadows. Ensure `@Image1`'s logo remains sharp and unwarped."

---

## 9. Real human faces & the asset library

**Direct upload of reference images/videos containing real human faces is blocked** — an anti-deepfake policy tightened at the 2.0 relaunch under legal pressure. Two sanctioned paths:

- **Virtual portraits** — AI-generated faces of people who don't exist can be registered/used freely.
- **Private/trusted asset library** — register an asset and receive a persistent `asset://<ID>` referenceable across many separate generations (ideal for episodic content: same face + clothing across shots). Real people must complete a one-time **liveness authentication**; virtual avatars need no review. Asset IDs are permanent, should be kept confidential, and real-person authentication does not migrate between providers.

Prompts naming specific celebrities, trademarked characters, or copyrighted styles are also restricted.

---

## 10. Clip continuation / extending past 15s

Two documented mechanisms:

**(a) `video-extend` endpoint** (`bytedance/seedance-2.0/video-extend`, plus a `-fast` variant): takes an existing **video** + a new prompt, analyzes the whole clip (trajectory, lighting, composition — not just the last frame), generates a fresh segment, and concatenates. Optional `last_image` sets a target end frame for the new segment. Output ratio matches the input; only the new segment is billed; extensions are chainable to evolve a narrative.

**(b) Manual `return_last_frame` chaining:** set `return_last_frame: true` on a generation; the response includes the clip's final frame image, which you feed back as the next call's `first_frame`/`image_url`. This is "last frame of clip N → first frame of clip N+1" stitching.

Practical guidance: consistency holds well for ~3–6 chained extensions (30–90s); beyond that, re-anchor with the original reference image. **Output URLs are temporary (~24h on some hosts)** — copy results to durable storage before chaining across sessions.

---

## 11. Example workflows

**Character-anchored reference-to-video (fal.ai):**
```python
result = fal_client.subscribe(
    "bytedance/seedance-2.0/reference-to-video",
    arguments={
        "prompt": "@Image1 walks confidently down a neon-lit city street at night, camera tracking alongside.",
        "image_urls": ["https://example.com/character-reference.jpg"],
        "resolution": "720p", "duration": "10", "aspect_ratio": "16:9",
        "generate_audio": True,
    },
)
```

**First + last frame (fal.ai — day→night transition):**
```python
result = fal_client.subscribe(
    "bytedance/seedance-2.0/image-to-video",
    arguments={
        "prompt": "Smooth transition from day to night, the sky gradually darkens as city lights turn on.",
        "image_url": "https://example.com/day.jpg",
        "end_image_url": "https://example.com/night.jpg",
        "resolution": "720p", "duration": "10", "aspect_ratio": "16:9",
    },
)
```

**Raw Ark-style first/last with `role`:**
```json
{
  "model": "doubao-seedance-2-0-260128",
  "content": [
    { "type": "text", "text": "The first frame is image 1 and the final frame is image 2, smooth continuous motion." },
    { "type": "image_url", "image_url": {"url": "https://.../pic1.jpg"}, "role": "first_frame" },
    { "type": "image_url", "image_url": {"url": "https://.../pic2.jpg"}, "role": "last_frame" }
  ]
}
```

**Multi-reference composition (character + environment + motion transfer):**
> "Reference `@Image1` for the man's appearance in `@Image2`'s elevator setting. Fully replicate `@Video1`'s camera movements and the protagonist's facial expressions. Hitchcock zoom when startled, then several orbit shots inside the elevator."

**Video editing / character replacement:**
> "Replace the woman in `@Video1` with `@Image1`. Keep the original camera movement and lighting."
