# Confirmation Gate (Phase 5)

The exact format for the single user-facing report at the end. This is the only point where the skill stops and asks.

## Report template

Print this to the user verbatim, with the placeholders filled in. Then ask the single question.

```markdown
# Auto-Research Result — <target-path>

## Artifact
- **Path**: <absolute path>
- **Type**: <skill-md | claude-md | subagent | slash-command | generic-prompt>
- **Lines before / after**: <N> → <M>
- **Workspace**: .auto-research/<target-name>/

## Score
<one of:>
- **Eval pass-rate**: <baseline_score> → <final_score> (Δ <delta>) over <N> iterations
- **Format-validation only**: PASS — <bullet list of what was checked>

## Iterations
| # | Hypothesis | Score | Decision |
|---|---|---|---|
| 0 | (baseline) | <baseline> | — |
| 1 | <one-line hypothesis> | <score> | keep / discard |
| 2 | … | … | … |
…

## Sources cited (deduped)
1. <URL> — <one-line context>
2. <URL> — <one-line context>
…

## Diff (preview)
```diff
<unified diff between baseline and final, max ~150 lines>
…
```
Full diff: `.auto-research/<target-name>/final.diff`

## Top changes (rationale)
1. **<change summary>** — <why> — source: <URL>
2. **<change summary>** — <why> — source: <URL>
3. **<change summary>** — <why> — source: <URL>
(Full rationale: `.auto-research/<target-name>/iteration-final/rationale.md`)
```

## The single question

Use the `AskUserQuestion` tool with one question and exactly three options:

- **Apply** — overwrite `<target-path>` with the final proposal
- **Discard** — leave the target untouched; keep the workspace for inspection
- **Iterate with feedback** — take a new constraint and run one more iteration

Phrase the question: *"Apply these changes to <target-name>?"*

## Apply path

When the user picks **Apply**:

1. Read `.auto-research/<target-name>/iteration-final.md` (or the best iteration's proposal.md)
2. Write it over the target file
3. If the project root is git-tracked, run `git add <target>` and produce a commit suggestion to the user (do NOT auto-commit unless the user explicitly enabled that — committing the user's project files is destructive enough to warrant a separate confirmation, even after Apply)
4. Write `.auto-research/<target-name>/RESULT.md` containing: timestamp, applied iteration number, final score, sources list
5. Print a one-line confirmation: "Applied iteration N to <target>. Workspace preserved at .auto-research/<target-name>/."

## Discard path

When the user picks **Discard**:

1. Do **not** touch the target file.
2. Print: "No changes applied. Workspace preserved at .auto-research/<target-name>/ for inspection."
3. Exit.

## Iterate-with-feedback path

When the user picks **Iterate with feedback**:

1. Use a free-text follow-up to capture the constraint (e.g., "the rewrite removed the example I rely on — keep the LinkedIn example section").
2. Append the constraint to `.auto-research/<target-name>/user_constraints.md`.
3. Re-enter Phase 3 with the constraint added to the rewrite rules, run **one** more iteration of Phase 4 (not the full loop), then re-enter Phase 5.

## Hard limit on iterate-with-feedback loops

If the user has picked "Iterate with feedback" three consecutive times without picking Apply or Discard, surface that explicitly:

> "We've iterated three times on your feedback without applying. The skill may be over-fitting. Options: (a) Apply the current version anyway, (b) Discard and start fresh, (c) Continue iterating (not recommended)."

Then ask once more. If the user picks (c), continue but warn that confidence is degrading.

## Format details

- The diff section uses standard unified-diff syntax. If the diff is over 150 lines, truncate with a `…` line and point to the full file.
- Sort sources by first appearance in `findings.md`, deduped.
- The hypotheses column in the iterations table should be the verbatim line written to `iterations.tsv` during the loop — do not paraphrase at report time.
