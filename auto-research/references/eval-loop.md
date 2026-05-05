# Karpathy-Style Eval Loop

Operational manual for the autonomous binary-assertion eval loop in Phase 4b. Modeled on Andrej Karpathy's `autoresearch` (`prepare.py` / `program.md` / `train.py` triad). Runs without stopping for user input.

## When to run this loop

Only when the artifact type is `skill-md` (always) or `generic-prompt` with user-supplied test inputs. For all other types, skip — see [artifact-types.md](artifact-types.md).

## Workspace structure

```
.auto-research/<target-name>/
├── baseline.md                    # Original artifact (locked, read-only)
├── research_topics.md
├── findings.md
├── evals.json                     # Binary assertions + test prompts (locked, read-only)
├── iterations.tsv                 # Append-only log
├── iteration-0/
│   └── outputs/                   # Baseline runs
│       ├── eval-1.md
│       ├── eval-2.md
│       └── ...
├── iteration-1/
│   ├── proposal.md                # Modified target artifact
│   ├── rationale.md
│   └── outputs/
└── ...
```

The baseline (`baseline.md`), the test specification (`evals.json`), and the scoring script (`scripts/score_evals.py`) are **locked**. The eval loop is only allowed to modify `iteration-N/proposal.md`. This is the equivalent of Karpathy's locked `prepare.py`.

## evals.json schema

```json
{
  "skill_name": "<target-name>",
  "test_prompts": [
    {
      "id": 1,
      "prompt": "User-style prompt that exercises the skill",
      "expected_behavior": "Plain-English description, used for human review only — not for scoring"
    }
  ],
  "assertions": [
    {
      "id": "A1",
      "text": "Output contains a fenced code block",
      "type": "binary"
    },
    {
      "id": "A2",
      "text": "Output is under 300 words",
      "type": "binary"
    }
  ]
}
```

Every test prompt is scored against every assertion → max score = `len(prompts) × len(assertions)`.

## Generating evals.json

Generate it once at the start of Phase 4b. Spawn a sub-agent (model: opus) with this prompt:

```
You are generating evals.json for the auto-research skill.

TARGET ARTIFACT (verbatim):
<paste full target artifact>

RESEARCH FINDINGS:
<paste findings.md>

Produce evals.json with:
- 5–8 test prompts that a real user would plausibly send to this skill / artifact.
- 6–12 binary assertions. Every assertion must be answerable strictly yes/no by reading the output text alone.

GOOD assertions:
- "Output contains a Markdown header starting with '# '"
- "Output is between 100 and 500 words"
- "Output contains the substring 'Source:' at least once"
- "Output does NOT contain em-dashes (—)"
- "Final non-empty line ends with a period, exclamation mark, or question mark"

BAD assertions (REJECT and rewrite):
- "Output is well-written" (subjective)
- "Output is helpful" (subjective)
- "Output is between 100 and 500 words AND contains a code block" (compound — split into two)
- Anything requiring an LLM judge

Rule: if you cannot determine pass/fail by mechanically inspecting the text in Python (regex, length, substring), the assertion is invalid.

Return ONLY the JSON, no commentary.
```

Save the result to `.auto-research/<target-name>/evals.json` and immediately mark it read-only:
- On Windows: `attrib +R evals.json`
- On Unix: `chmod 444 evals.json`

(The lock is advisory — its real purpose is to remind the loop not to touch it.)

## The autonomous loop instruction

Once `evals.json` is in place, baseline runs are captured (iteration-0/outputs/), and the baseline score is in `iterations.tsv`, hand the loop to the main agent with this exact instruction:

```
You are running the auto-research eval loop on <target-path>. The eval spec is .auto-research/<target>/evals.json. The scorer is scripts/score_evals.py.

For each iteration N (starting at 1):
1. Read iteration-(N-1)/proposal.md (or baseline.md for N=1) and findings.md.
2. Form ONE hypothesis — a single specific change to the artifact (one section, one rule, one field). Append it as the iteration's hypothesis line in iterations.tsv.
3. Write iteration-N/proposal.md with that single change applied.
4. Replace the target file with iteration-N/proposal.md (so when the skill is invoked it uses the new version).
5. For each test_prompt in evals.json, run the skill / artifact against the prompt and capture output to iteration-N/outputs/eval-<id>.md. Run prompts in parallel where possible.
6. Run: py scripts/score_evals.py --evals .auto-research/<target>/evals.json --outputs .auto-research/<target>/iteration-N/outputs/  → captures pass_rate.
7. Compare pass_rate to previous best (initially the baseline score):
   - If strictly better → KEEP. git add .auto-research/<target>/iteration-N + the modified target file. git commit -m "iter N: keep — <hypothesis>". Append "keep" to iterations.tsv with new score.
   - If equal or worse → DISCARD. git checkout -- <target>. Restore previous-best version of target. Append "discard" to iterations.tsv.
8. Continue to iteration N+1.

STOP CONDITIONS — and ONLY these:
- pass_rate reaches 1.0
- Iteration counter reaches 10
- 5 consecutive discards in a row (signal that the search has saturated)
- A hard error blocks further runs (out of disk, git failure, etc.)

DO NOT pause to ask the user "should I keep going?" or "is this a good stopping point?". DO NOT ask for confirmation between iterations. Run autonomously until a stop condition fires.

When you stop, write iteration-final.md as a copy of the best iteration's proposal.md and update iterations.tsv with the final stop reason.
```

This instruction block is intentionally close to the wording shown in the Karpathy autoresearch tutorial videos — the autonomous tone is what makes the loop run without pleading for permission every iteration.

## Why iteration cap = 10 (hard stop 15)

Past ~10–15 iterations, observed across multiple practitioner writeups, the loop tends to **degrade** quality even as the binary score improves: prompts grow bloated with one-off overrides that conflict with each other. Cap at 10 by default; allow user to raise to 15 with `--max-iterations 15` flag wording in their request, never higher unless they justify it.

## Scoring rules (deterministic)

The scorer (`scripts/score_evals.py`) reads each output file and each assertion, decides pass/fail, and writes `score.json` to the iteration folder.

Assertion types currently supported:

| Pattern in `text` | How it's scored |
|---|---|
| "contains the substring '<X>'" | substring search |
| "does NOT contain '<X>'" | negated substring search |
| "matches the regex `<X>`" | re.search |
| "does NOT match the regex `<X>`" | negated re.search |
| "is under N words" / "is over N words" | word count comparison |
| "is between N and M words" | word count range |
| "contains at least N <occurrences of X>" | substring count threshold |
| "starts with `<X>`" / "ends with `<X>`" | startswith / endswith |
| "first line <predicate>" / "last line <predicate>" | apply predicate to that line |

Anything outside this vocabulary is **rejected at evals.json validation time** with an error that points the user back to this list. This keeps assertions honest — if you can't express it as one of these patterns, it isn't binary.

## What to do when the loop fails

- **Hard error mid-iteration** → restore baseline target, log the failure in iterations.tsv with `decision=error`, exit Phase 4b, jump to Phase 5 with the partial result and the error message included in the report.
- **5 consecutive discards** → the search has saturated. Stop and report the best-so-far iteration. The user can decide in Phase 5 whether to accept it.
- **Score regressed and we cannot recover the previous-best target file** (git error) → halt the loop, do **not** continue, surface a hard error to Phase 5 with the workspace state intact for manual recovery.

## Things the loop must never do

- Modify `evals.json` (locked)
- Modify `scripts/score_evals.py` (locked)
- Skip git commits between keeps (the iteration trail is the recovery mechanism)
- Bundle multiple changes into one iteration (violates the one-variable rule)
- Use a Likert-scale or LLM-judge assertion (binary only)
