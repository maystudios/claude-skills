# Research Strategies

How to extract research topics, run parallel sub-agent research, and rank sources.

## Source authority ranking (apply when sub-agents return conflicting evidence)

1. **Anthropic official documentation** — `docs.claude.com/*`, `code.claude.com/*`, `platform.claude.com/*`, `anthropic.com/engineering/*`
2. **anthropics/skills repository** — official skill examples, especially `skill-creator/SKILL.md`
3. **Anthropic engineering blog posts** (anthropic.com/engineering)
4. **Authoritative community sources** — Langfuse, Braintrust, well-known Anthropic-adjacent practitioners (Lee Hanchung, Jason Liu, Hamel Husain), official Claude Code release notes
5. **Independent technical writeups** with reproducible code (Medium, dev.to, personal blogs) — only if no higher-tier source is available
6. **Discussion / Reddit / Twitter** — last resort, only as a tiebreaker between equally cited sources

When sub-agents return tier-1 evidence, ignore lower-tier conflicts. When the only source is tier 4 or below, mark the topic as **medium-confidence** and surface that to Phase 5.

## Topic-extraction checklist by artifact type

For each artifact type, generate research topics from this checklist (skip topics that don't apply to the specific target):

### `skill-md` checklist

- [ ] Current `description` field length limit and trigger-accuracy heuristics
- [ ] Frontmatter fields supported by Claude Code in 2026 beyond `name` + `description`
- [ ] Progressive disclosure conventions (when to split SKILL.md → references)
- [ ] anthropics/skills style conventions for skills in the same domain
- [ ] Whether "When to Use This Skill" body sections are deprecated
- [ ] How parallel sub-agent invocation currently works (relevant if the skill uses `Agent` tool)
- [ ] Deprecated patterns visible in the target body (model names, tool names, frontmatter fields)
- [ ] Skill-creator's current "draft → test → iterate → optimize" loop (if the target's workflow overlaps)

### `claude-md` checklist

- [ ] Current "include / exclude" guidance
- [ ] Length target and warning thresholds
- [ ] Memory architecture in 2026 (auto-memory, MEMORY.md, agent memory)
- [ ] Import (`@path`) syntax — depth limits, supported variants
- [ ] Project vs. user CLAUDE.md interaction (which wins, how they merge)
- [ ] Whether any sections in the target have grown into procedures (smell — should become a skill)

### `subagent` checklist

- [ ] Current `tools` field syntax and value vocabulary
- [ ] Whether new frontmatter fields exist in 2026 (`model`, `effort`, `context`, etc.)
- [ ] Best practices for sub-agent `description` triggering
- [ ] Whether to specify `model` explicitly or inherit
- [ ] Whether the sub-agent body should reproduce instructions or rely on a referenced skill

### `slash-command` checklist

- [ ] Current slash-command authoring conventions and template features
- [ ] Whether `$ARGUMENTS` or similar substitution patterns are still standard
- [ ] Frontmatter fields supported

### `generic-prompt` checklist

Build the checklist dynamically from the prompt's content. Identify each non-trivial claim, technique, tool reference, or framework mention in the prompt — each becomes a topic.

## Sub-agent prompt template

Pass this exact structure to each parallel `Agent` call (substitute `<topic>`):

```
You are a research sub-agent for the auto-research skill. Investigate ONE topic and return findings in a strict format.

TOPIC: <topic>

Procedure:
1. Run 2–4 WebSearch queries with the current year (2026). Phrase queries to surface authoritative sources first.
2. WebFetch the most authoritative pages from the source authority ranking:
   tier 1: docs.claude.com, code.claude.com, platform.claude.com, anthropic.com/engineering
   tier 2: github.com/anthropics/skills
   tier 3: Anthropic engineering blog posts
   tier 4: well-known practitioner writeups (Langfuse, Braintrust, Lee Hanchung, etc.)
3. Synthesize. Quote verbatim where the wording is load-bearing. Cite every quote with its URL.

Return EXACTLY this format and nothing else:

### Topic: <topic>
**Verdict:** <1–3 sentence answer>
**Evidence:**
- "..." — <URL>
- "..." — <URL>
**Confidence:** high | medium | low
**Implications for rewrite:** <1–2 sentences on how this should change the target artifact>

If you cannot find any tier-1 to tier-3 source, set Confidence to "low" and explain in Implications why the rewrite should NOT rely on this topic.

Word budget: under 250 words total.
```

## Parallelization rules

- Spawn all topic agents **in a single message** with multiple `Agent` tool calls. Do not send them serially.
- Use `general-purpose` subagent_type and model `sonnet` for each.
- Each topic gets its own agent — do not bundle two topics into one agent.
- Cap: 12 topics. If you generated more than 12, prune to the most rewrite-relevant 12.

## Anti-patterns

- **Don't** research the artifact's domain in depth (e.g., for a PDF skill, don't research "PDF tools 2026"). Research the *meta-question* of how to write a good skill for that domain.
- **Don't** trust a single non-Anthropic source for a claim that contradicts the artifact's existing approach. Get a second source or downgrade confidence.
- **Don't** discard the target's project-specific conventions just because a generic best-practice differs. Project-specific content (custom workflows, German prose, internal terminology) must survive the rewrite unless the user said otherwise.
