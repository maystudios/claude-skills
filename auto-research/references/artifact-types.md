# Artifact Types — Detection, Constraints, and Eval Eligibility

This file is the single source of truth for **what kind of artifact** is being improved and **which rules apply**. Read this in Phase 0 (classification) and Phase 4 (validation strategy).

## Quick decision table

| Type | Detection | Eval-loop eligible? | Format validation |
|---|---|---|---|
| `skill-md` | File named `SKILL.md`, has YAML frontmatter with `name` + `description`, sits in `<dir>/SKILL.md` | **Yes** | Strict |
| `claude-md` | File named `CLAUDE.md` or `CLAUDE.local.md` (any directory) | No (skip-eval) | Lenient |
| `subagent` | File path matches `.claude/agents/*.md`, frontmatter has `name` + `description` (and usually `tools` / `model`) | No (skip-eval) | Strict |
| `slash-command` | File path matches `.claude/commands/*.md` | No (skip-eval) | Lenient |
| `generic-prompt` | Anything else — `.md` files containing prompts/instructions/system-messages | Yes **iff** user supplies test inputs in their request, otherwise No | Lenient |

## Per-type rules

### `skill-md`

**Format constraints** (all enforced in Phase 4a):

- YAML frontmatter at top with at minimum `name:` and `description:`
- `description` field ≤ 1024 characters (Anthropic doc limit; combined with optional `when_to_use` cap is 1,536 — but `when_to_use` is being phased out in favour of merging into `description`)
- `description` written in **third person**, "Use when …" pattern, front-loads the key trigger
- Body markdown (after frontmatter) ≤ 500 lines — split to references if longer
- References live one level deep in `references/<file>.md` — no nested references-of-references
- Forward slashes only in any path (no Windows backslashes)
- No "When to Use This Skill" header in the body — that information must live in the `description` field, because the body is only loaded after the skill triggers

**What to research** (Phase 1 topic checklist):

- Current `description` field constraints and trigger-accuracy patterns
- Current frontmatter fields supported by Claude Code in 2026 (anything beyond `name` and `description`?)
- Progressive disclosure best practices
- Recent additions to anthropics/skills repo style conventions
- Any deprecated patterns in the target's body (e.g. "When to Use This Skill" sections)

### `claude-md`

**Format constraints**:

- Total length ≤ 200 lines is the official guidance; warn between 200–250, fail above 250
- No nested imports past one level (`@path/to/file` is OK; `@path/to/file` that itself imports another `@…` path is OK; deeper recursion is a smell)
- Prefer Bash commands the model can't guess, code-style rules that differ from defaults, repo etiquette
- Cut anything Claude can infer from reading code

**What to research**:

- Current "what to include / exclude" guidance from Anthropic
- Memory architecture changes in 2026 (auto-memory, MEMORY.md, agent memory)
- Import syntax (`@path` form) — supported variants, depth limits
- Project vs. user CLAUDE.md hierarchy — recent changes

**Why no eval loop**: CLAUDE.md has no measurable output of its own — its effect is "did Claude do the right thing in the next session," which is unobservable inside this skill's loop. Format validation is the right ceiling.

### `subagent`

**Format constraints**:

- Frontmatter: `name`, `description`, optional `tools` (space-separated), optional `model` (e.g. `sonnet`, `opus`, `haiku`)
- `description` third-person, "Use when …" pattern, includes trigger phrases
- Body: clear, focused instructions for the sub-agent's task
- File path: `.claude/agents/<name>.md` (project) or `~/.claude/agents/<name>.md` (user)

**What to research**:

- Current `tools` syntax and any new fields in 2026
- Sub-agent description trigger patterns
- When to set `model` explicitly vs. inheriting

**Why no eval loop**: Sub-agent definitions are short and their "output" is whatever the spawned agent does on a real task — too variable to score with binary assertions in a tight loop.

### `slash-command`

**Format constraints**:

- Optional YAML frontmatter (some commands have none)
- Reasonable length (< 200 lines)
- Clear single purpose
- File path: `.claude/commands/<name>.md`

**What to research**:

- Current slash-command authoring conventions
- Any frontmatter fields supported in 2026
- How `$ARGUMENTS` substitution and similar template features work currently

### `generic-prompt`

Catch-all. Format validation is line-count + heading-structure sanity only.

Eval loop runs **only** if the user supplies, in their original request to the auto-research skill, a set of test inputs (e.g. "and run it against these 5 example queries"). Without test inputs, default to skip-eval.

**What to research**:

- Whatever the prompt's domain is — extract the topic from the prompt's content and research it directly.

## Detection algorithm (Phase 0)

```
1. If path ends with /SKILL.md → skill-md
2. Else if filename is CLAUDE.md or CLAUDE.local.md → claude-md
3. Else if path contains /.claude/agents/ → subagent
4. Else if path contains /.claude/commands/ → slash-command
5. Else → generic-prompt
```

If detection is ambiguous (e.g., a file called `SKILL.md` outside a skills directory), prefer the stricter type and surface the ambiguity to the user once at the start, then continue.
