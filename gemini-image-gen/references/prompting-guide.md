# Gemini Image Generation - Complete Prompting Guide

Source: [Google Cloud Blog - Ultimate Prompting Guide for Nano Banana](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana?hl=en)

## 2D Pixel Art Game Asset Prompting

### Sprite Generation Formula

`[Subject] + [Perspective] + [Pixel Art Style] + [Color Palette] + [Background] + [Resolution]`

**Example prompts for game assets:**

> Generate a single deciduous tree in full spring bloom with fresh bright green leaves and a sturdy brown trunk. Top-down 3/4 view game asset. Style: 32-pixel art sprite, top-down 3/4 perspective, warm and vibrant color palette, thick black outlines, no anti-aliasing, soft ambient lighting, SNES-era aesthetic, Stardew Valley inspired. Isolated on a solid, flat, uniform magenta background, hex #FF00FF. The entire background must be a single pure magenta color with zero variation. Flat, even, uniform lighting. Generate in 1K resolution. Aspect ratio 1:1.

> Create a wooden treasure chest, slightly open with gold coins visible inside and a subtle glow effect. Front-facing 3/4 view pixel art game sprite. 16-bit retro style, limited color palette, crisp pixels, no anti-aliasing, thick dark outlines. Isolated on a solid, flat, uniform magenta background, hex #FF00FF. Flat, even, uniform lighting. Generate in 1K resolution. Aspect ratio 1:1.

> Design a set of 4 potion bottles (red health, blue mana, green stamina, yellow speed) as pixel art game items. Each bottle has a unique shape and cork stopper. 32-pixel art style, vibrant saturated colors, black outlines, no anti-aliasing, RPG game aesthetic. Isolated on a solid, flat, uniform magenta background, hex #FF00FF. Flat, even, uniform lighting. Generate in 1K resolution.

### Tileable Texture Formula

`[Material/Surface] + [Seamless/Tileable] + [Perspective] + [Pixel Art Style] + [Resolution]`

> Create a seamless tileable grass texture for a top-down pixel art RPG. Multiple shades of green with occasional small flowers and dirt patches. 32-pixel art style, SNES-era aesthetic, no anti-aliasing. The texture must tile seamlessly in all directions. Generate in 1K resolution. Aspect ratio 1:1.

### Character Sprite Formula

`[Character Description] + [Pose/Action] + [View Direction] + [Pixel Art Style] + [Background]`

> A fantasy knight character in silver armor with a blue cape, holding a sword in ready stance. Side-view pixel art game sprite, 32-pixel style, NES/SNES era aesthetic, limited 16-color palette, thick black outlines, no anti-aliasing. Isolated on a solid, flat, uniform magenta background, hex #FF00FF. Flat, even, uniform lighting. Generate in 1K resolution. Aspect ratio 1:1.

### Key Style Descriptors for Pixel Art

| Term | Effect |
|------|--------|
| "no anti-aliasing" | Crisp pixel edges, no smoothing |
| "thick black outlines" | Clear sprite boundaries |
| "limited color palette" | Retro feel, e.g., "16-color palette" |
| "SNES-era aesthetic" | 16-bit style reference |
| "NES-era aesthetic" | 8-bit style reference |
| "top-down 3/4 view" | Classic RPG perspective (Stardew Valley, Zelda) |
| "side-view" | Platformer perspective |
| "isometric" | Isometric game perspective |
| "solid, flat, uniform magenta background, hex #FF00FF" | Chroma key removal (default, best results) |
| "solid, flat, uniform chromakey green background, hex #00FF00" | Alternative chroma key for magenta sprites |
| "isolated on pure white background" | Legacy fallback, use --bg-color white |

### Perspectives by Game Type

| Game Type | Perspective |
|-----------|------------|
| Top-down RPG | Top-down 3/4 view |
| Platformer | Side view |
| Strategy/City builder | Isometric |
| UI/Inventory items | Front-facing, flat |

---

## Models

| Model | Base | Max Input Tokens | Max Output Tokens |
|-------|------|-----------------|-------------------|
| Nano Banana Pro | Gemini 3 Pro Image | 65,536 | 32,768 |
| Nano Banana 2 | Gemini 3.1 Flash Image | 131,072 | 32,768 |

## Resolution Options

| Model | Available Resolutions |
|-------|----------------------|
| Nano Banana Pro | 1K, 2K, 4K |
| Nano Banana 2 | 0.5K (512px), 1K, 2K, 4K |

## Aspect Ratios

**Both models:** 1:1, 3:2, 2:3, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9

**Nano Banana 2 additionally:** 1:4, 4:1, 1:8, 8:1

## Reference Images

- Up to **14 reference object images** per prompt
- Supported formats: PNG, JPEG, WebP, HEIC, HEIF
- Use for: character consistency, product placement, style transfer, composition guidance, sketch-to-render

## Five Prompting Frameworks

---

### Framework 1: Image Generation

#### Text-to-Image (without references)

**Formula:** `[Subject] + [Action] + [Location/Context] + [Composition] + [Style]`

**Example:**
> [Subject] A striking fashion model wearing a tailored brown dress, sleek boots, and holding a structured handbag. [Action] Posing with a confident, statuesque stance, slightly turned. [Location/context] A seamless, deep cherry red studio backdrop. [Composition] Medium-full shot, center-framed. [Style] Fashion magazine style editorial, shot on medium-format analog film, pronounced grain, high saturation, cinematic lighting effect.

#### Multimodal Generation (with references)

**Formula:** `[Reference images] + [Relationship instruction] + [New scenario]`

Use for maintaining character consistency and merging products into new environments.

**Example:**
> Using the attached napkin sketch as the structural layout and the attached fabric sample as the surface texture, transform this into a high-fidelity 3D render of a modern armchair placed in a Scandinavian-style living room.

---

### Framework 2: Image Editing

#### Conversational Editing (without new references)

**Semantic masking (inpainting):** Define a "mask" through text to edit a specific part of an image.

- Be explicit about what to keep exactly the same
- Example: "Remove the man from the photo, keeping the background and lighting identical"

#### Composition and Style Transfer (with new references)

**Adding elements:**
- Upload a base image and an object image
- Tell the model to combine them
- Example: "Place this product on the desk in the base image"

**Style transfer:**
- Upload a photo and request a style change
- Example: "Recreate the exact content of this city street photo in the style of a Van Gogh painting"

---

### Framework 3: Real-Time Information from Web Search

The model can search the web for real-time data and use it in image generation.

**Formula:** `[Source/Search request] + [Analytical task] + [Visual translation]`

**Example:**
> Search for the current weather in San Francisco, then generate an image of the Golden Gate Bridge reflecting those exact weather conditions in a photorealistic style.

---

### Framework 4: Text Rendering and Localization

**Rules for best typographic results:**

1. **Use quotes:** Enclose desired text in quotes
   - Example: `"Happy Birthday"` or `"URBAN EXPLORER"`

2. **Choose a font:** Describe the typography style or name
   - Examples: "bold, white, sans-serif font" or "Century Gothic 12px font"

3. **Translate and localize:** Write in one language, specify target language
   - Supports 10+ languages

**Text-first hack:** First converse to generate text concepts, then request the image with that text.

**Example prompts:**
> A high-end, glossy commercial beauty shot of a sleek, minimalist nude-colored face moisturizer jar resting on a warm studio background. The lighting is soft and radiant. Next to the product, render three lines of text with the following exact styling: For the top line, the word "GLOW" in a flowing, elegant Brush Script font. For the middle line, the text "10% OFF" in a heavy, blocky Impact font. For the bottom line, the text "Your First Order" in a thin, minimalist Century Gothic font.

> A typographic poster with a solid black background, bold letters spell "New York", filling the center of the frame. The text acts as a cut-out window. A photograph of the New York skyline is visible ONLY inside the letterforms.

---

### Framework 5: Prompting Like a Creative Director

#### 1. Design Your Lighting

| Lighting Type | Effect |
|---------------|--------|
| Three-point softbox setup | Even, professional product lighting |
| Chiaroscuro (harsh, high contrast) | Dramatic, moody, artistic |
| Golden hour backlighting | Warm, long shadows, romantic |
| Rembrandt lighting | Portrait classic, triangle shadow on cheek |
| Ring light | Beauty, fashion, even face lighting |
| Neon / colored gels | Cyberpunk, editorial, modern |

#### 2. Choose Camera, Lens, and Focus

| Camera/Lens | Visual Effect |
|-------------|--------------|
| GoPro | Immersive, distorted, action feel |
| Fujifilm | Authentic color science, film-like |
| Cheap disposable camera | Raw, nostalgic flash aesthetic |
| Low-angle, shallow DOF (f/1.8) | Subject isolation, dramatic perspective |
| Wide-angle lens | Vast scale, environmental shots |
| Macro lens | Intricate details, close-up textures |
| Telephoto (200mm) | Compressed background, portrait isolation |
| Tilt-shift | Miniature effect, selective focus |

#### 3. Define Color Grading and Film Stock

| Style | Description |
|-------|-------------|
| 1980s color film, slightly grainy | Nostalgic, gritty, retro |
| Cinematic muted teal tones | Modern, moody, cinematic |
| High saturation editorial | Vibrant, fashion magazine |
| Kodak Portra 400 | Warm skin tones, soft pastels |
| Fuji Velvia 50 | Hyper-saturated landscapes |
| Black and white, high contrast | Dramatic, timeless |
| Cross-processed | Unexpected color shifts, experimental |

#### 4. Emphasize Materiality and Texture

Instead of generic descriptions, specify exact materials:

| Generic | Enhanced |
|---------|----------|
| "suit jacket" | "navy blue tweed suit jacket with visible herringbone weave" |
| "armor" | "ornate elven plate armor, etched with silver leaf patterns" |
| "coffee mug" | "minimalist ceramic coffee mug with a matte sage green glaze" |
| "wall" | "exposed brick wall with peeling whitewash and moss growth" |
| "floor" | "polished white marble floor with subtle grey veining" |

---

## Best Practices Summary

1. **Be specific** -- Provide concrete details on subject, lighting, and composition
2. **Use positive framing** -- Describe what you want, not what you don't want ("empty street" instead of "no cars")
3. **Control the camera** -- Use photographic/cinematic terms like "low angle" and "aerial view"
4. **Iterate** -- Refine images with follow-up prompts in the same conversation
5. **Start with a strong verb** -- Begin prompts with a verb describing the primary operation
6. **Describe narratively** -- Write scene descriptions, not keyword lists
7. **Specify resolution and aspect ratio** -- Include these in the prompt text naturally
8. **Use reference images strategically** -- Combine up to 14 references for character consistency, style transfer, or composition

---

## Integration Capabilities

- **Gemini + Veo:** Create keyframes with image gen, then generate video between them
- **Gemini + Lyria:** Generate visuals, then add custom AI soundtrack
- **Web Search:** Models can use real-time web data for generation context

## Trust and Safety

- All generated images include **C2PA Content Credentials**
- All generated images include a **SynthID watermark**
