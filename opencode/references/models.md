# OpenCode Model Selection Guide

## Model ID Format

Always `provider/model-id`. Use `opencode models` to list currently available models.

## Recommended Models by Task

### Implementation (Code Generation)

| Model | Speed | Quality | Cost | When to use |
|-------|-------|---------|------|-------------|
| `openai/gpt-5.4` | Medium | Excellent | $$ | Default for most implementation tasks |
| `openai/gpt-5.3-codex` | Medium | Excellent | $$ | Code-optimized, great for complex refactors |
| `openai/gpt-5.4-mini` | Fast | Good | $ | Simpler tasks, boilerplate generation |
| `openai/gpt-5.4-mini-fast` | Very fast | Good | $ | Quick edits, straightforward changes |
| `google/gemini-3-pro` | Medium | Very good | $$ | Alternative perspective, strong reasoning |
| `google/gemini-2.5-pro` | Medium | Very good | $$ | Proven, reliable |
| `github-copilot/gpt-5.4` | Medium | Excellent | Free* | With Copilot subscription |
| `github-copilot/gpt-5.3-codex` | Medium | Excellent | Free* | With Copilot subscription |

### Code Review

| Model | Best for |
|-------|----------|
| `openai/gpt-5.4` + `--variant high` | Deep review, catches subtle bugs |
| `openai/gpt-5.3-codex` + `--variant high` | Code-focused review with deep reasoning |
| `google/gemini-3-pro` | Different perspective from Claude |
| `openai/gpt-5.4-mini` | Quick sanity check |

### Debugging / Root Cause Analysis

| Model | Best for |
|-------|----------|
| `openai/gpt-5.3-codex` | Deep code reasoning |
| `openai/gpt-5.4` + `--variant high` | Complex multi-file bugs |
| `google/gemini-2.5-pro` | Alternative diagnostic approach |

### Research / Exploration

| Model | Best for |
|-------|----------|
| `openai/gpt-5.4-mini-fast` | Fast codebase exploration |
| `openai/gpt-5.4-fast` | Quick answers with good quality |
| `google/gemini-2.5-flash` | Very fast, cost-effective |

### Local / Offline Models

| Model | Requirements |
|-------|-------------|
| `ollama/qwen3-coder:latest` | Ollama running, good for privacy |
| `lmstudio/qwen/qwen3-coder-30b` | LM Studio running |
| `lmstudio/qwen/qwen3-coder-next` | LM Studio running, latest Qwen |

## Reasoning Effort Variants

Use `--variant <level>` to control reasoning depth. Values are provider-specific free-form strings:

| Variant | Provider | Effect | Use when |
|---------|----------|--------|----------|
| `minimal` | OpenAI | Minimal reasoning | Simple, routine tasks |
| `medium` | OpenAI | Moderate reasoning | Standard tasks |
| `high` | OpenAI, Anthropic, Google | Deep reasoning | Complex bugs, architecture review |
| `xhigh` | OpenAI | Extra high reasoning | Hardest problems |
| `max` | Anthropic, Google | Maximum reasoning | Hardest problems |

Not all variants work with all providers. Use `high` as a safe default across providers.

## Provider Authentication

| Provider | Auth method |
|----------|------------|
| OpenAI | `opencode providers login` (OAuth) or `OPENAI_API_KEY` |
| Google | `GEMINI_API_KEY` env var |
| GitHub Copilot | `opencode providers login` (device OAuth) |
| Ollama | No auth (local) |
| LM Studio | No auth (local) |

## Cost Considerations

- `github-copilot/*` models are included with a Copilot subscription (no extra cost)
- `openai/gpt-5.4-mini-fast` and `openai/gpt-5.4-fast` are the cheapest OpenAI options
- `google/gemini-2.5-flash` is very cost-effective for research tasks
- Local models (Ollama, LM Studio) have zero API cost but require GPU resources
- OpenCode Zen free tier models: `opencode/big-pickle`, `opencode/nemotron-3-super-free`
