# OpenCode Model Selection Guide

## Model ID Format

Always `provider/model-id`. Use `opencode models` to list currently available models.

**Supported providers:** OpenAI, GitHub Copilot, OpenCode (free tier), local models (Ollama, LM Studio).

**Not available:** Google/Gemini and Anthropic/Claude models are not available in OpenCode.

## Recommended Models by Task

### Implementation (Code Generation)

| Model | Speed | Quality | Cost | When to use |
|-------|-------|---------|------|-------------|
| `openai/gpt-5.4` | Medium | Excellent | $$ | Default for most implementation tasks |
| `openai/gpt-5.3-codex` | Medium | Excellent | $$ | Code-optimized, great for complex refactors |
| `openai/gpt-5.4-mini` | Fast | Good | $ | Simpler tasks, boilerplate generation |
| `openai/gpt-5.4-mini-fast` | Very fast | Good | $ | Quick edits, straightforward changes |
| `github-copilot/gpt-5.4` | Medium | Excellent | Free* | With Copilot subscription |
| `github-copilot/gpt-5.3-codex` | Medium | Excellent | Free* | With Copilot subscription |

### Code Review

| Model | Best for |
|-------|----------|
| `openai/gpt-5.4` + `--variant high` | Deep review, catches subtle bugs |
| `openai/gpt-5.3-codex` + `--variant high` | Code-focused review with deep reasoning |
| `openai/gpt-5.4-mini` | Quick sanity check |

### Debugging / Root Cause Analysis

| Model | Best for |
|-------|----------|
| `openai/gpt-5.3-codex` | Deep code reasoning |
| `openai/gpt-5.4` + `--variant high` | Complex multi-file bugs |
| `openai/gpt-5.4` + `--variant xhigh` | Hardest problems |

### Research / Exploration

| Model | Best for |
|-------|----------|
| `openai/gpt-5.4-mini-fast` | Fast codebase exploration |
| `openai/gpt-5.4-fast` | Quick answers with good quality |
| `openai/gpt-5.4` | Thorough analysis |

### Local / Offline Models

| Model | Requirements |
|-------|-------------|
| `ollama/qwen3-coder:latest` | Ollama running, good for privacy |
| `lmstudio/qwen/qwen3-coder-30b` | LM Studio running |
| `lmstudio/qwen/qwen3-coder-next` | LM Studio running, latest Qwen |

### OpenCode Free Tier

| Model | Notes |
|-------|-------|
| `opencode/big-pickle` | Free, no API key needed |
| `opencode/nemotron-3-super-free` | Free, no API key needed |

## Reasoning Effort Variants

Use `--variant <level>` to control reasoning depth:

| Variant | Provider | Effect | Use when |
|---------|----------|--------|----------|
| `minimal` | OpenAI | Minimal reasoning | Simple, routine tasks |
| `medium` | OpenAI | Moderate reasoning | Standard tasks |
| `high` | OpenAI | Deep reasoning | Complex bugs, architecture review |
| `xhigh` | OpenAI | Extra high reasoning | Hardest problems |

Not all variants work with all models. Use `high` as a safe default for deep analysis.

## Provider Authentication

| Provider | Auth method |
|----------|------------|
| OpenAI | `opencode providers login` (OAuth) or `OPENAI_API_KEY` |
| GitHub Copilot | `opencode providers login` (device OAuth) |
| Ollama | No auth (local) |
| LM Studio | No auth (local) |
| OpenCode Free | No auth needed |

## Cost Considerations

- `github-copilot/*` models are included with a Copilot subscription (no extra cost)
- `openai/gpt-5.4-mini-fast` and `openai/gpt-5.4-fast` are the cheapest OpenAI options
- Local models (Ollama, LM Studio) have zero API cost but require GPU resources
- OpenCode free-tier models (`opencode/big-pickle`, `opencode/nemotron-3-super-free`) cost nothing

## Dynamic Model Discovery

The available models change as OpenCode updates. Always use `opencode models` to see
what's currently available. This guide lists common models but the actual list may differ.
