#!/usr/bin/env python3
"""Parse OpenCode `--format json` ndjson output and extract useful information.

Usage:
    opencode run --format json ... | python parse_output.py
    opencode run --format json ... | python parse_output.py --mode text
    opencode run --format json ... | python parse_output.py --mode full
    opencode run --format json ... | python parse_output.py --mode tools
    opencode run --format json ... | python parse_output.py --mode cost
    opencode run --format json ... | python parse_output.py --mode session
    opencode run --format json ... | python parse_output.py --mode diff
    opencode run --format json ... | python parse_output.py --mode summary

Modes:
    text    - Extract only the model's text response (default)
    full    - Show text + tool calls + tool results
    tools   - Show only tool calls and results
    cost    - Show token usage and cost summary
    session - Extract session ID for continuation
    diff    - Extract file modifications from tool calls
    summary - One-line summary (status, tokens, cost)
"""

import json
import sys
import argparse
import re
import time


def parse_events(lines):
    """Parse ndjson lines into structured events."""
    events = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def extract_text(events):
    """Extract concatenated text response."""
    parts = []
    for ev in events:
        if ev.get("type") == "text":
            text = ev.get("part", {}).get("text", "")
            if text:
                parts.append(text)
    return "".join(parts) if parts else "(no text response)"


def extract_full(events):
    """Extract text, tool calls, and tool results."""
    output = []
    for ev in events:
        t = ev.get("type", "")
        part = ev.get("part", {})
        if t == "text":
            text = part.get("text", "")
            if text:
                output.append(text)
        elif t == "tool_call":
            name = part.get("name", "unknown")
            inp = part.get("input", {})
            output.append(f"\n--- Tool Call: {name} ---")
            output.append(json.dumps(inp, indent=2, ensure_ascii=False))
        elif t == "tool_result":
            result = part.get("output", "")
            output.append(f"--- Tool Result ---")
            output.append(str(result)[:2000])
    return "\n".join(output)


def extract_tools(events):
    """Extract only tool calls and results."""
    output = []
    for ev in events:
        t = ev.get("type", "")
        part = ev.get("part", {})
        if t == "tool_call":
            name = part.get("name", "unknown")
            inp = part.get("input", {})
            output.append(f"[CALL] {name}: {json.dumps(inp, ensure_ascii=False)[:500]}")
        elif t == "tool_result":
            result = str(part.get("output", ""))
            output.append(f"[RESULT] {result[:500]}")
    return "\n".join(output) if output else "(no tool calls)"


def extract_cost(events):
    """Extract token usage and cost from step_finish events."""
    total_input = 0
    total_output = 0
    total_reasoning = 0
    total_cost = 0.0
    steps = 0

    for ev in events:
        if ev.get("type") == "step_finish":
            part = ev.get("part", {})
            tokens = part.get("tokens", {})
            total_input += tokens.get("input", 0)
            total_output += tokens.get("output", 0)
            total_reasoning += tokens.get("reasoning", 0)
            total_cost += part.get("cost", 0)
            steps += 1

    lines = [
        f"Steps: {steps}",
        f"Input tokens: {total_input:,}",
        f"Output tokens: {total_output:,}",
        f"Reasoning tokens: {total_reasoning:,}",
        f"Total tokens: {total_input + total_output + total_reasoning:,}",
        f"Cost: ${total_cost:.4f}",
    ]
    return "\n".join(lines)


def extract_session(events):
    """Extract session ID from step_start or step_finish events for continuation."""
    session_id = None
    for ev in events:
        if ev.get("type") == "step_start":
            sid = ev.get("sessionID") or ev.get("part", {}).get("sessionID")
            if sid:
                session_id = sid
        elif ev.get("type") == "step_finish":
            sid = ev.get("sessionID") or ev.get("part", {}).get("sessionID")
            if sid:
                session_id = sid
    return session_id if session_id else "(no session ID found)"


def extract_diff(events):
    """Extract file modifications from tool calls (write, edit, patch operations)."""
    modifications = []
    write_tools = {"write", "write_file", "Write", "create", "Create"}
    edit_tools = {"edit", "edit_file", "Edit", "patch", "Patch", "replace", "Replace"}
    bash_tools = {"bash", "Bash", "shell", "Shell"}

    for ev in events:
        if ev.get("type") != "tool_call":
            continue
        part = ev.get("part", {})
        name = part.get("name", "")
        inp = part.get("input", {})

        if name in write_tools:
            path = inp.get("file_path") or inp.get("path") or inp.get("filePath", "")
            content_preview = str(inp.get("content", ""))[:200]
            modifications.append(f"[WRITE] {path}")
            if content_preview:
                modifications.append(f"  preview: {content_preview}...")

        elif name in edit_tools:
            path = inp.get("file_path") or inp.get("path") or inp.get("filePath", "")
            old = str(inp.get("old_string") or inp.get("old", ""))[:100]
            new = str(inp.get("new_string") or inp.get("new", ""))[:100]
            modifications.append(f"[EDIT] {path}")
            if old:
                modifications.append(f"  old: {old}")
            if new:
                modifications.append(f"  new: {new}")

        elif name in bash_tools:
            cmd = str(inp.get("command") or inp.get("cmd", ""))
            # Detect file-modifying bash commands
            if any(kw in cmd for kw in [">>", "> ", "mv ", "cp ", "mkdir ", "rm ", "sed ", "tee "]):
                modifications.append(f"[BASH] {cmd[:200]}")

    if not modifications:
        return "(no file modifications detected)"
    return "\n".join(modifications)


def extract_summary(events):
    """One-line summary: status | tokens | cost | text length."""
    text = extract_text(events)
    has_text = text != "(no text response)"

    total_tokens = 0
    total_cost = 0.0
    tool_calls = 0

    for ev in events:
        if ev.get("type") == "step_finish":
            tokens = ev.get("part", {}).get("tokens", {})
            total_tokens += tokens.get("input", 0) + tokens.get("output", 0) + tokens.get("reasoning", 0)
            total_cost += ev.get("part", {}).get("cost", 0)
        elif ev.get("type") == "tool_call":
            tool_calls += 1

    status = "ok" if has_text else "empty"
    text_len = len(text) if has_text else 0
    return f"{status} | {total_tokens:,} tokens | ${total_cost:.4f} | {tool_calls} tool calls | {text_len:,} chars"


def main():
    parser = argparse.ArgumentParser(description="Parse OpenCode JSON output")
    parser.add_argument(
        "--mode",
        choices=["text", "full", "tools", "cost", "session", "diff", "summary"],
        default="text",
        help="Output mode (default: text)",
    )
    args = parser.parse_args()

    lines = sys.stdin.readlines()
    events = parse_events(lines)

    if not events:
        print("(no output received from OpenCode)", file=sys.stderr)
        sys.exit(1)

    extractors = {
        "text": extract_text,
        "full": extract_full,
        "tools": extract_tools,
        "cost": extract_cost,
        "session": extract_session,
        "diff": extract_diff,
        "summary": extract_summary,
    }

    print(extractors[args.mode](events))


if __name__ == "__main__":
    main()
