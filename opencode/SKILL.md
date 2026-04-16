---
name: opencode
description: >
  Invoke OpenCode CLI as a sub-agent to leverage alternative AI models (GPT-5.x, Codex, Gemini,
  local models) for code implementation, review, debugging, research, and second opinions.
  Use when the user asks to "use opencode", "get a second opinion from GPT/Codex/Gemini",
  "implement with opencode", "review with opencode", "let opencode handle this",
  "use a different model", or wants cross-model validation. Also triggers when the user
  explicitly names an OpenCode model (e.g., "use gpt-5.4", "use codex", "use gemini-3-pro")
  or wants to delegate a task to a non-Claude AI system. Supports all providers configured
  in the user's OpenCode installation (OpenAI, Google, GitHub Copilot, local models via
  Ollama/LM Studio).
---

# OpenCode Sub-Agent Integration

Invoke OpenCode CLI headlessly from Claude Code to leverage alternative AI models for implementation,
review, debugging, and research tasks.

## Prerequisites

- `opencode` CLI installed and in PATH (verify: `opencode --version`)
- At least one provider authenticated (`opencode providers list`)
- Available models listed via `opencode models`

## Core Command

```bash
opencode run [message..] --format json --model <provider/model> --dir <working-dir> --dangerously-skip-permissions
```

Key flags:
- `--format json` -- machine-parseable ndjson output (always use this)
- `--model provider/model` -- e.g., `openai/gpt-5.4`, `google/gemini-3-pro`
- `--variant <level>` -- provider-specific reasoning effort (e.g., `minimal`, `high`, `max`; OpenAI also supports `medium`, `xhigh`)
- `--dir <path>` -- working directory for the task
- `--dangerously-skip-permissions` -- auto-approve tool calls (required for headless)
- `-f/--file <path>` -- attach file(s) to the prompt
- `--agent <name>` -- select agent (`build` for implementation, `plan` for analysis)
- `-c/--continue` -- continue last session
- `-s/--session <id>` -- continue specific session

## Output Parsing

The `--format json` flag emits ndjson (one JSON object per line). Key event types:

| type | Contains |
|------|----------|
| `text` | `.part.text` -- the model's text response |
| `tool_call` | `.part.name`, `.part.input` -- tool invocations |
| `tool_result` | `.part.output` -- tool execution results |
| `step_start` | Session/message IDs |
| `step_finish` | `.part.tokens` (usage), `.part.cost`, `.part.reason` |

Extract the response text (always redirect stderr to avoid corrupting JSON):
```bash
opencode run --format json ... 2>/dev/null | python .claude/skills/opencode/scripts/parse_output.py
```

Or inline with jq (if installed):
```bash
opencode run --format json ... 2>/dev/null | jq -r 'select(.type=="text") | .part.text'
```

## Workflow

Determine the task type from the user's request, then follow the matching workflow below.

### 1. Implement -- Code generation or modification

Use when the user wants OpenCode to write or modify code.

1. Select model (default: `openai/gpt-5.4` or user-specified)
2. Gather context: identify relevant files the model needs to see
3. Construct a detailed prompt including:
   - The task description
   - Relevant file contents or paths (use `-f` for key files)
   - Project conventions from CLAUDE.md
   - Specific constraints or patterns to follow
4. Run with `--agent build` (use Bash tool with `timeout: 300000`):
   ```bash
   OPENCODE_DISABLE_AUTOUPDATE=true opencode run --format json --model <model> --agent build --dir "<project-dir>" --dangerously-skip-permissions -f <file1> -f <file2> "<detailed task prompt>" 2>/dev/null
   ```
5. Parse the JSON output: pipe through `python .claude/skills/opencode/scripts/parse_output.py`
6. Review the changes OpenCode made (read modified files, verify correctness)
7. Report results to user, highlighting what was changed. Revert anything incorrect.

### 2. Review -- Code review and quality analysis

Use when the user wants a second opinion on code quality, bugs, or correctness.

1. Select model (default: `openai/gpt-5.4` for deep review, `openai/gpt-5.4-mini` for quick)
2. Identify files to review
3. Construct review prompt:
   ```
   Review the following code for: correctness, potential bugs, performance issues,
   security vulnerabilities, and adherence to best practices.
   Be specific about line numbers and suggest concrete fixes.
   ```
4. Run with `--agent plan` (read-only analysis, Bash `timeout: 300000`):
   ```bash
   OPENCODE_DISABLE_AUTOUPDATE=true opencode run --format json --model <model> --agent plan --dir "<project-dir>" --dangerously-skip-permissions -f <file1> "<review prompt>" 2>/dev/null
   ```
5. Parse and present the review findings to the user

### 3. Debug -- Bug investigation and diagnosis

Use when the user wants OpenCode to investigate a bug or error.

1. Select model (default: `openai/gpt-5.3-codex` for deep reasoning)
2. Gather error messages, stack traces, and relevant code
3. Construct diagnostic prompt with full context
4. Run with `--agent plan` (Bash `timeout: 300000`):
   ```bash
   OPENCODE_DISABLE_AUTOUPDATE=true opencode run --format json --model <model> --agent plan --dir "<project-dir>" --dangerously-skip-permissions "<diagnostic prompt with error details>" 2>/dev/null
   ```
5. Parse findings and present root cause analysis

### 4. Research -- Codebase exploration and architecture analysis

Use when the user wants OpenCode to explore and analyze the codebase.

1. Select model (default: `openai/gpt-5.4-mini-fast` for speed)
2. Construct research question
3. Run (Bash `timeout: 300000`):
   ```bash
   OPENCODE_DISABLE_AUTOUPDATE=true opencode run --format json --model <model> --agent plan --dir "<project-dir>" --dangerously-skip-permissions "<research question>" 2>/dev/null
   ```
4. Parse and summarize findings

## Model Selection Guide

Pick the right model for the task. See `references/models.md` for the full guide.

**Quick defaults:**
- Implementation: `openai/gpt-5.4` or `openai/gpt-5.3-codex`
- Review: `openai/gpt-5.4` with `--variant high`
- Quick tasks: `openai/gpt-5.4-mini-fast`
- Deep reasoning: `openai/gpt-5.3-codex` with `--variant high`
- Cost-sensitive: `github-copilot/gpt-5.4` (included with Copilot subscription)
- Local/offline: `ollama/qwen3-coder:latest` or `lmstudio/qwen/qwen3-coder-30b`
- Google models: `google/gemini-3-pro` or `google/gemini-2.5-pro`

## Prompt Engineering

OpenCode has NO access to this conversation's context. Prompts must be fully self-contained --
include all relevant information, file contents, and constraints in the prompt itself.

Do NOT use OpenCode to invoke Claude models (e.g., `github-copilot/claude-opus-4.6`) -- use Claude directly instead.

When constructing prompts for OpenCode, always include:

1. **Task clarity** -- exactly what to do, in imperative form
2. **File context** -- attach relevant files with `-f` or describe paths
3. **Constraints** -- coding conventions, patterns, naming rules from CLAUDE.md
4. **Output format** -- tell the model what form the answer should take
5. **Scope limits** -- what NOT to change, boundaries of the task. Be explicit about which directories to search ("Check ONLY AbilitySystem/", "Do NOT explore other directories"). Broad prompts cause timeouts.

For UE5/VHS project tasks, prepend this context block:
```
This is an Unreal Engine 5.7 C++ project (VHS). Key conventions:
- GAS naming: GA_ (abilities), GC_ (cues), MMC_ (magnitude calcs), GE_ (effects)
- UE prefixes: A (actors), U (UObjects), F (structs), E (enums), I (interfaces)
- Headers and .cpp live side-by-side (no Public/Private split)
- Module: VHS, dependencies in VHS.Build.cs
```

## Error Handling

- If `opencode` is not found: inform user to install (`npm i -g opencode`)
- If no providers configured: inform user to run `opencode providers login`
- If model not available: fall back to `opencode models` output and suggest alternatives
- If command times out (>3 min): reduce scope or use a faster model
- If JSON parsing fails: fall back to `--format default` and read raw text output

## Advanced Patterns

See `references/advanced.md` for:
- Server mode for persistent sessions
- Multi-step workflows with session continuation
- Parallel model comparison (same prompt to multiple models)
- Custom agent configurations
