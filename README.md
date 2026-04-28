# Claude Code Skills by maystudios

A curated collection of production-ready [Claude Code](https://claude.ai/code) skills for game development, AI tooling, media processing, audio/MIDI workflows, and C++ programming. Built from real-world experience shipping an Unreal Engine 5.7 horror game.

## Skills

### Unreal Engine 5

| Skill | What it does |
|-------|-------------|
| **[unreal-gas](./unreal-gas/)** | Expert guide for UE5 Gameplay Ability System — ASC, abilities, effects, attributes, tags, cues, prediction, and replication |
| **[unreal-best-practices](./unreal-best-practices/)** | Modern UE5 development — GAS, Enhanced Input, StateTree, PCG, CommonUI, World Partition, naming conventions |
| **[unreal-thirdparty](./unreal-thirdparty/)** | Integrating third-party C/C++ libraries — static/dynamic linking, Build.cs, cross-platform, ABI pitfalls |
| **[unreal-pcg-python](./unreal-pcg-python/)** | PCG (Procedural Content Generation) Python integration — PCGPythonInterop plugin, custom nodes, editor automation |

### AI & LLM Integration

| Skill | What it does |
|-------|-------------|
| **[opencode](./opencode/)** | Use OpenCode CLI as a sub-agent — delegate tasks to GPT-5.x, Codex, Gemini, or local models for implementation, review, and debugging |
| **[llama-cpp](./llama-cpp/)** | Complete llama.cpp guide — C API, GGUF, quantization, GPU backends, HTTP server, grammar constraints, UE5 integration |

### Image & Asset Generation

| Skill | What it does |
|-------|-------------|
| **[gemini-image-gen](./gemini-image-gen/)** | Generate images via Google Gemini — resolution control (0.5K-4K), reference images, style transfer, text rendering, inpainting |
| **[2d-pixel-asset](./2d-pixel-asset/)** | Generate 2D pixel art game assets — sprites, tilesets, background removal, rasterization to exact pixel dimensions |

### Video & Media Processing

| Skill | What it does |
|-------|-------------|
| **[video-download](./video-download/)** | Download videos from YouTube, Instagram, TikTok, Twitter/X, and 1000+ platforms as MP4 |
| **[link-download](./link-download/)** | Download videos as MP4 or extract audio as MP3 from 1000+ platforms via yt-dlp |
| **[video-summarizer](./video-summarizer/)** | Analyze local MP4 files with Gemini API and generate structured Markdown summaries |
| **[video-fetch-and-summarize](./video-fetch-and-summarize/)** | Download videos from URLs and auto-generate Markdown summaries with Gemini |

### Audio & Music

| Skill | What it does |
|-------|-------------|
| **[audio-to-midi](./audio-to-midi/)** | Transcribe MP3/WAV/FLAC to MIDI + MusicXML — Basic Pitch and high-accuracy Piano model, optional Demucs stem separation, tempo/key/chord analysis |
| **[midi-synth](./midi-synth/)** | Render MIDI/MusicXML to WAV/MP3 with FluidSynth and convert to Strudel live-coding patterns — ghost-note cleaning, tempo/transpose, instrument override |
| **[google-ai-studio-tts](./google-ai-studio-tts/)** | Generate speech, podcasts, and multi-speaker dialogue with Google AI Studio's Gemini Flash TTS — drives the live web app via Chrome (claude-in-chrome MCP) |

### Web Development

| Skill | What it does |
|-------|-------------|
| **[tech-product-landing](./tech-product-landing/)** | Build production-grade landing pages — dark theme, Framer Motion animations, Vite + React + TypeScript + Tailwind |

### Research & Knowledge Capture

| Skill | What it does |
|-------|-------------|
| **[anthropic-skilljar-extractor](./anthropic-skilljar-extractor/)** | Extract any Anthropic Academy (Skilljar) course into a structured Markdown folder — one file per lesson, downloaded diagrams, organized by section |

## Quick Install

```bash
# Install all skills at once
npx skills add maystudios/claude-skills

# Or pick individual skills
npx skills add maystudios/claude-skills/opencode
npx skills add maystudios/claude-skills/unreal-gas
npx skills add maystudios/claude-skills/gemini-image-gen
npx skills add maystudios/claude-skills/video-summarizer
npx skills add maystudios/claude-skills/audio-to-midi
npx skills add maystudios/claude-skills/midi-synth
```

## What are Claude Code Skills?

Skills are modular packages that extend [Claude Code](https://claude.ai/code) with specialized domain knowledge, workflows, and tools. They transform Claude from a general-purpose coding agent into a domain expert — without fine-tuning.

Each skill is a folder with a `SKILL.md` file containing instructions that Claude loads on demand. Skills can also bundle scripts, reference docs, and assets.

Learn more: [Claude Code Skills Documentation](https://docs.anthropic.com/en/docs/claude-code/skills)

## Contributing

Found a bug or have an improvement? PRs welcome. Each skill lives in its own directory — just edit the relevant `SKILL.md` or `references/` files.

## License

[MIT](./LICENSE)
