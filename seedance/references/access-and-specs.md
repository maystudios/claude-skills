# Seedance 2.0 — Access, Specs & API

Reference for how to reach the model, exact limits, model IDs, the raw request shape, pricing, and safety restrictions. Facts are current as of **mid-2026**; figures marked *(reseller)* come from third-party host/aggregator docs, not a primary ByteDance source — verify against a live console before quoting cost.

## Contents
1. What it is & version lineage
2. Access routes
3. Model IDs
4. Specs
5. Request shape (raw API + fal parameters)
6. Pricing
7. Safety & IP restrictions
8. Impostor-site warning

---

## 1. What it is & version lineage

Seedance 2.0 is ByteDance's flagship video model, from the **ByteDance Seed** team. Official launch blog **12 Feb 2026**; technical report arXiv:2604.14148. It is a **unified multimodal audio-video model** (text + image + audio + video inputs → video with synchronized audio).

- **Seedance 1.0** (Jun 2025) — 1080p, silent (no audio), T2V + I2V, multi-shot.
- **Seedance 1.5 Pro** (Dec 2025) — introduced native joint audio-video.
- **Seedance 2.0** (Feb 2026) — unified 4-modality input, major audio quality/expressiveness upgrade (dual-channel stereo), video editing/extension, ~30% faster *(vendor claim)*. **This is the current generally-available flagship.**
- **Seedance 2.5** — announced Jun 2026 (30s clips, up to 50 references, native 4K) but **closed enterprise beta**, not public GA as of this writing. Don't assume a user has it.

Official variants of 2.0: **Standard**, **Fast** (lower latency/cost), **Mini** (cheapest/lightest, ~Jun 2026). "Pro"/"Lite" labels seen on reseller sites are **not** official ByteDance naming for the 2.0 line.

---

## 2. Access routes

| Route | Type | Notes |
|-------|------|-------|
| **Dreamina** (dreamina.capcut.com) | Official, international consumer | Free daily credits (~2–3 gens/day); model picker → Seedance 2.0 / 2.0 Fast |
| **Jimeng 即梦** (jimeng.jianying.com) | Official, China consumer | Requires +86 phone / Douyin login |
| **Volcano Engine Ark** (`https://ark.cn-beijing.volces.com/api/v3`) | Official API, China | POST to `/contents/generations/tasks`, then poll for completion |
| **BytePlus ModelArk** (`https://ark.ap-southeast.bytepluses.com/api/v3`) | Official API, international | International equivalent of Ark |
| **fal.ai** | Official hosted partner | Separate endpoints for text-to-video / image-to-video / reference-to-video / video-extend; best host-level docs |
| **Replicate** | Third-party host | Hosts `bytedance/seedance-2.0` and `-mini` |
| OpenRouter, WaveSpeed, Kie, PiAPI, Runware, AI/ML API, etc. | Aggregators | Public reseller routes; price/reliability vary |

---

## 3. Model IDs

- **Volcano Engine (China):** `doubao-seedance-2-0-260128` (standard), `doubao-seedance-2-0-fast-260128` (fast), `doubao-seedance-2-0-mini-260615` (mini)
- **BytePlus (international):** `dreamina-` prefix, e.g. `dreamina-seedance-2-0-mini-260615`
- **fal.ai:** `bytedance/seedance-2.0/text-to-video`, `.../image-to-video`, `.../reference-to-video`, `.../video-extend` (+ `-fast` variants)

---

## 4. Specs

| Property | Value |
|----------|-------|
| Native resolution | 480p, 720p |
| Higher resolution | 1080p and native 4K on hosting platforms *(4K added Jun 2026; secondary-sourced)* |
| Duration | 4–15 s (or `auto`) |
| Frame rate | 24 fps *(well-supported, not an explicitly labeled official spec)* |
| Aspect ratios | `auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16` |
| Modes | T2V, I2V (± end frame), reference-to-video, multi-shot, video-extend/editing |
| Reference limits | ≤9 images + ≤3 videos (≤15s comb.) + ≤3 audio (≤15s comb.); **12 files total** |
| Image files | JPEG/PNG/WebP/BMP/TIFF/GIF/HEIC/HEIF, <30 MB, aspect 0.4–2.5, 300–6000 px/side |
| Video refs | MP4/MOV, 2–15s combined, <50 MB, 480–720p input |
| Audio refs | MP3/WAV, ≤15s combined, ≤15 MB each |
| Output | MP4 with synchronized stereo audio; URLs often expire ~24h |

---

## 5. Request shape

**Raw ByteDance/Ark style** — a `content` array of typed items; images carry a `role` (`first_frame` / `last_frame` / `reference_image`), videos `reference_video`, audio `reference_audio`:

```json
{
  "model": "doubao-seedance-2-0-260128",
  "content": [
    { "type": "text", "text": "@Image1 walks down a neon street, camera tracking. 10s, 16:9." },
    { "type": "image_url", "image_url": {"url": "https://.../char.jpg"}, "role": "reference_image" }
  ]
}
```
Documented request-body fields include: `resolution`, `ratio`, `duration`, `seed`, `watermark`, `generate_audio`, `return_last_frame`. There is **no** documented `negative_prompt` field, and the 1.x-only `frames` / `camera_fixed` are unsupported in 2.0.

**fal.ai parameters** (per endpoint): `prompt`, `image_url` / `image_urls`, `end_image_url`, `audio_url` / `audio_urls`, `resolution`, `duration`, `aspect_ratio`, `generate_audio` (default true), `seed`. Ark is async (submit task → poll); fal exposes a `subscribe` helper that waits.

---

## 6. Pricing

Highly channel-dependent; there is no single canonical number.
- **Volcano Engine (official, China):** ~**$0.14/second** of output *(TechNode)*.
- **fal.ai:** ~$0.24/s (720p Fast) → $0.30/s (720p standard) → ~$0.68/s (1080p T2V); reference-to-video with a video input drops to ~$0.18/s. Token option ~$0.014/1k tokens (≤1080p), ~$0.008/1k (4K). *(reseller/host)*
- **Consumer apps:** Dreamina free daily credits; low-cost paid trials reported on Jimeng.
- Audio adds **no cost** (on or off, same price).

---

## 7. Safety & IP restrictions

- **No real human faces as direct references** — use virtual portraits or the liveness-authenticated asset library (`asset://<ID>`). See `references-and-frames.md` §9.
- Prompts naming **celebrities, trademarked characters, or copyrighted styles** are blocked (safeguards added Feb 2026 after cease-and-desist letters from Disney, Paramount, and the MPA).
- On-screen **text/typography renders poorly** — add captions in post.
- Closed model: **no open weights, no LoRA/fine-tuning.**
- Content filter reportedly evaluates whole-scene intent (LLM-based, not keyword matching); film-production vocabulary (shot types, lens, lighting) tends to be judged with more latitude than plain narrative descriptions of the same scene.

---

## 8. Impostor-site warning

Domains like `seedance2.ai`, `seedance2.app`, and `seedance.tv` are **not** official ByteDance properties despite ranking in search. Treat any non-ByteDance / Volcengine / BytePlus / Dreamina / fal domain as unofficial before entering payment or account credentials.
