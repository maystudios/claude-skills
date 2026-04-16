# Advanced OpenCode Patterns

## Server Mode (Persistent Sessions)

Avoid cold-boot overhead by running OpenCode as a persistent server:

```bash
# Start server in background
OPENCODE_DISABLE_AUTOUPDATE=true opencode serve --port 4096 &

# Send tasks to the running server (fast, no cold boot)
opencode run --attach http://localhost:4096 --format json --dangerously-skip-permissions "task"
```

Check if server is running:
```bash
curl -s http://localhost:4096/health 2>/dev/null && echo "running" || echo "not running"
```

Use server mode when running multiple sequential tasks to avoid the 2-5s cold boot per invocation.

## Session Continuation (Multi-Step Workflows)

Continue a previous session to build on prior context:

```bash
# First task - capture session ID
SESSION_ID=$(opencode run --format json --model openai/gpt-5.4 --dangerously-skip-permissions \
  "Analyze the architecture of the interaction system" 2>/dev/null \
  | python .claude/skills/opencode/scripts/parse_output.py --mode session)

# Follow-up using same session (agent retains context from step 1)
opencode run --format json --session "$SESSION_ID" --dangerously-skip-permissions \
  "Now suggest improvements based on your analysis" 2>/dev/null \
  | python .claude/skills/opencode/scripts/parse_output.py
```

Or simply continue the last session:
```bash
opencode run --format json --continue --dangerously-skip-permissions "Follow up on previous task"
```

## Parallel Multi-Model Comparison

Run the same prompt against multiple models to compare results:

```bash
PROMPT="Review this file for bugs and security issues"
DIR="C:/UnrealEngine/VHS"

# Run in parallel
opencode run --format json --model openai/gpt-5.4 --variant high --agent plan --dir "$DIR" \
  --dangerously-skip-permissions -f Source/VHS/Player/HorrorCharacter.cpp \
  "$PROMPT" 2>/dev/null > /tmp/review_gpt54.txt &

opencode run --format json --model openai/gpt-5.3-codex --variant high --agent plan --dir "$DIR" \
  --dangerously-skip-permissions -f Source/VHS/Player/HorrorCharacter.cpp \
  "$PROMPT" 2>/dev/null > /tmp/review_codex.txt &

wait

# Parse and compare
echo "=== GPT-5.4 ==="
cat /tmp/review_gpt54.txt | python .claude/skills/opencode/scripts/parse_output.py
echo -e "\n=== Codex 5.3 ==="
cat /tmp/review_codex.txt | python .claude/skills/opencode/scripts/parse_output.py
```

Issues raised by 2+ models have higher confidence than single-model findings.

## Implement-Then-Review Pipeline

The core quality assurance pattern. Implement with one model, review with another:

```bash
DIR="C:/UnrealEngine/VHS"

# Step 1: Implement
opencode run --format json --model openai/gpt-5.4 --agent build --dir "$DIR" \
  --dangerously-skip-permissions \
  "[CONTEXT] UE5.7 C++ project... [TASK] Implement GA_Crouch..." \
  2>/dev/null | tee /tmp/impl_output.txt | python .claude/skills/opencode/scripts/parse_output.py --mode diff

# Step 2: Review the changes with a different model
IMPL_RESULT=$(cat /tmp/impl_output.txt | python .claude/skills/opencode/scripts/parse_output.py)
opencode run --format json --model openai/gpt-5.3-codex --variant high --agent plan --dir "$DIR" \
  --dangerously-skip-permissions \
  "Review this implementation for correctness and UE5 best practices: $IMPL_RESULT" \
  2>/dev/null | python .claude/skills/opencode/scripts/parse_output.py
```

## Autonomous Improvement Loop (CLI)

Run the test harness in autoresearch loop mode:

```bash
# Run tests repeatedly, tracking best scores
python .claude/skills/opencode/scripts/test_skill.py --loop --max-iter 5

# Loop with specific model and test
python .claude/skills/opencode/scripts/test_skill.py --loop --model openai/gpt-5.4 --test review

# Full comparison across models
python .claude/skills/opencode/scripts/test_skill.py --compare --all
```

The loop mode:
- Tracks best scores per model/test (ratchet pattern from autoresearch)
- Stops early if all tests reach 100%
- Logs every iteration to results.tsv for analysis
- Can be interrupted with Ctrl+C

## Git-Checkpoint Pattern

Use git as a state machine for safe implementation:

```bash
# 1. Save current state
git stash

# 2. Let OpenCode implement
opencode run --format json --model openai/gpt-5.4 --agent build --dir "$DIR" \
  --dangerously-skip-permissions "Implement feature X" 2>/dev/null \
  | python .claude/skills/opencode/scripts/parse_output.py --mode diff

# 3. Check what changed
git diff --name-only

# 4. If bad, revert
git checkout -- .

# 5. If good, keep
git add -A && git commit -m "feat: implemented X via opencode/gpt-5.4"
```

## Background Agent Spawning

When Claude Code needs to continue working while OpenCode runs:

```bash
# Run in background, redirect to file
OPENCODE_DISABLE_AUTOUPDATE=true opencode run --format json \
  --model openai/gpt-5.4 --agent plan \
  --dir "C:/UnrealEngine/VHS" --dangerously-skip-permissions \
  "Deep architecture review of GAS integration" \
  2>/dev/null > /tmp/opencode_bg_result.txt
```

Use Bash `run_in_background: true` in Claude Code. When notified of completion:
```bash
cat /tmp/opencode_bg_result.txt | python .claude/skills/opencode/scripts/parse_output.py
```

## Model Fallback Chain

Automatic recovery when a model fails:

```bash
# Try primary model, fall back on failure
for MODEL in openai/gpt-5.4 openai/gpt-5.3-codex openai/gpt-5.4-mini-fast github-copilot/gpt-5.4; do
  RESULT=$(opencode run --format json --model "$MODEL" --agent plan --dir "$DIR" \
    --dangerously-skip-permissions "$PROMPT" 2>/dev/null)
  if echo "$RESULT" | python .claude/skills/opencode/scripts/parse_output.py --mode summary | grep -q "^ok"; then
    echo "$RESULT" | python .claude/skills/opencode/scripts/parse_output.py
    break
  fi
  echo "[$MODEL] failed, trying next..."
done
```

Or use the test harness `run_with_fallback()` function programmatically.

## File Attachment Patterns

```bash
# Single file
opencode run --format json --model openai/gpt-5.4 -f Source/VHS/Player/HorrorCharacter.h "Review this"

# Multiple files for cross-file analysis
opencode run --format json --model openai/gpt-5.4 \
  -f Source/VHS/AbilitySystem/VHSAbilitySystemComponent.h \
  -f Source/VHS/AbilitySystem/VHSAbilitySystemComponent.cpp \
  -f Source/VHS/AbilitySystem/Abilities/GA_Sprint.h \
  "Review how the ASC integrates with sprint ability"
```

## Custom Agent Selection

```bash
# build agent: full filesystem + bash access (for implementation)
opencode run --agent build --model openai/gpt-5.4 --dangerously-skip-permissions "Implement X"

# plan agent: read-only analysis (for review/research/debug)
opencode run --agent plan --model openai/gpt-5.4 --dangerously-skip-permissions "Analyze X"
```

## Environment Variables for Automation

| Variable | Purpose |
|----------|---------|
| `OPENCODE_DISABLE_AUTOUPDATE=true` | Prevent update prompts mid-task |
| `OPENCODE_DANGEROUSLY_SKIP_PERMISSIONS=true` | Global auto-approve (alternative to CLI flag) |
| `OPENCODE_CONFIG_CONTENT='{"permission":{"*":"allow"}}'` | Inline config override |
| `OPENCODE_LOG_LEVEL=ERROR` | Suppress non-error logs |

## Timeout Handling

1. Use faster models for time-sensitive tasks (`gpt-5.4-mini-fast`, `gpt-5.4-fast`)
2. Reduce scope with explicit constraints in prompt
3. Set explicit Bash timeout:
   ```bash
   timeout 180 opencode run --format json ... || echo "Timed out"
   ```

## Export and Import Sessions

```bash
opencode export <session-id> > session_backup.json
opencode import session_backup.json
```

## Stats and Cost Tracking

```bash
opencode stats --days 7 --models    # Usage by model
opencode stats --days 7 --tools     # Tool usage breakdown
```

## Parse Script Quick Reference

```bash
# Text only (default)
... | python parse_output.py

# Full output with tool calls
... | python parse_output.py --mode full

# Tool calls only (debug agent behavior)
... | python parse_output.py --mode tools

# Token/cost breakdown
... | python parse_output.py --mode cost

# Extract session ID for continuation
... | python parse_output.py --mode session

# See file modifications
... | python parse_output.py --mode diff

# One-line status summary
... | python parse_output.py --mode summary
```
