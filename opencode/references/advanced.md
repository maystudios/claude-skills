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

## Session Continuation (Multi-Step Workflows)

Continue a previous session to build on prior context:

```bash
# First task - get the session ID from step_finish event
SESSION_ID=$(opencode run --format json --model openai/gpt-5.4 --dangerously-skip-permissions \
  "Analyze the architecture of the interaction system" 2>/dev/null \
  | jq -r 'select(.type=="step_finish") | .sessionID' | tail -1)

# Follow-up using same session
opencode run --format json --session "$SESSION_ID" --dangerously-skip-permissions \
  "Now suggest improvements based on your analysis"
```

Or simply continue the last session:
```bash
opencode run --format json --continue --dangerously-skip-permissions "Follow up on previous task"
```

## Parallel Model Comparison

Run the same prompt against multiple models to compare results:

```bash
# Run in parallel (bash background jobs)
PROMPT="Review this file for bugs and security issues"
DIR="C:/UnrealEngine/VHS"

opencode run --format json --model openai/gpt-5.4 --agent plan --dir "$DIR" \
  --dangerously-skip-permissions -f Source/VHS/Player/HorrorCharacter.cpp \
  "$PROMPT" > "$TEMP/review_gpt54.json" 2>/dev/null &

opencode run --format json --model google/gemini-3-pro --agent plan --dir "$DIR" \
  --dangerously-skip-permissions -f Source/VHS/Player/HorrorCharacter.cpp \
  "$PROMPT" > "$TEMP/review_gemini.json" 2>/dev/null &

wait

# Parse both results
echo "=== GPT-5.4 Review ==="
cat "$TEMP/review_gpt54.json" | python scripts/parse_output.py --mode text

echo "=== Gemini 3 Pro Review ==="
cat "$TEMP/review_gemini.json" | python scripts/parse_output.py --mode text
```

## File Attachment Patterns

Attach specific files for context:

```bash
# Single file review
opencode run --format json --model openai/gpt-5.4 -f src/main.cpp "Review this file"

# Multiple files
opencode run --format json --model openai/gpt-5.4 \
  -f src/header.h -f src/impl.cpp \
  "Review these files for consistency"
```

## Custom Agent Selection

OpenCode has built-in agents:
- `build` -- full filesystem + bash access (for implementation)
- `plan` -- read-only analysis mode (for review/research)

```bash
# Implementation (can modify files)
opencode run --agent build --model openai/gpt-5.4 --dangerously-skip-permissions "Implement X"

# Analysis only (read-only)
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

OpenCode tasks can take significant time for complex operations. Strategies:

1. Use faster models for time-sensitive tasks (`gpt-5.4-mini-fast`, `gemini-2.5-flash`)
2. Reduce scope -- smaller prompts with fewer files
3. Set explicit Bash timeout when invoking:
   ```bash
   timeout 180 opencode run --format json ... || echo "Timed out after 3 minutes"
   ```

## Export and Import Sessions

```bash
# Export a session for archival
opencode export <session-id> > session_backup.json

# Import a session
opencode import session_backup.json
```

## Stats and Cost Tracking

```bash
# View usage stats
opencode stats --days 7 --models

# View tool usage breakdown
opencode stats --days 7 --tools
```
