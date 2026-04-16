# Claude Code Skills by maystudios

A curated collection of production-ready [Claude Code](https://claude.ai/code) skills for game development, AI tooling, and C++ workflows. Built from real-world experience shipping an Unreal Engine 5.7 horror game.

## Skills

### Game Development

| Skill | What it does |
|-------|-------------|
| **[unreal-gas](./unreal-gas/)** | Expert guide for UE5 Gameplay Ability System — covers ASC, abilities, effects, attributes, tags, cues, prediction, and replication patterns |
| **[unreal-best-practices](./unreal-best-practices/)** | Modern UE5 development guide — GAS, Enhanced Input, StateTree, PCG, CommonUI, World Partition, naming conventions, and the "research first" philosophy |
| **[unreal-thirdparty](./unreal-thirdparty/)** | Integrating third-party C/C++ libraries into UE5 — static/dynamic linking, Build.cs, cross-platform, ABI pitfalls |

### AI & LLM Integration

| Skill | What it does |
|-------|-------------|
| **[opencode](./opencode/)** | Use OpenCode CLI as a sub-agent inside Claude Code — delegate tasks to GPT-5.x, Codex, Gemini, or local models for implementation, review, debugging, and cross-model validation |
| **[llama-cpp](./llama-cpp/)** | Complete guide for llama.cpp — C API, GGUF format, quantization, GPU backends, HTTP server, embeddings, grammar constraints, and UE5 integration |

## Quick Install

```bash
# Install all skills at once
npx skills add maystudios/claude-skills

# Or pick individual skills
npx skills add maystudios/claude-skills/opencode
npx skills add maystudios/claude-skills/unreal-gas
npx skills add maystudios/claude-skills/unreal-best-practices
npx skills add maystudios/claude-skills/unreal-thirdparty
npx skills add maystudios/claude-skills/llama-cpp
```

## What are Claude Code Skills?

Skills are modular packages that extend [Claude Code](https://claude.ai/code) with specialized domain knowledge, workflows, and tools. They transform Claude from a general-purpose coding agent into a domain expert — without fine-tuning.

Each skill is a folder with a `SKILL.md` file containing instructions that Claude loads on demand. Skills can also bundle scripts, reference docs, and assets.

Learn more: [Claude Code Skills Documentation](https://docs.anthropic.com/en/docs/claude-code/skills)

## Contributing

Found a bug or have an improvement? PRs welcome. Each skill lives in its own directory — just edit the relevant `SKILL.md` or `references/` files.

## License

[MIT](./LICENSE)
