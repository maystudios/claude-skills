#!/usr/bin/env python3
"""Parse OpenCode `--format json` ndjson output and extract useful information.

Usage:
    opencode run --format json ... | python parse_output.py
    opencode run --format json ... | python parse_output.py --mode text
    opencode run --format json ... | python parse_output.py --mode full
    opencode run --format json ... | python parse_output.py --mode tools
    opencode run --format json ... | python parse_output.py --mode cost

Modes:
    text   - Extract only the model's text response (default)
    full   - Show text + tool calls + tool results
    tools  - Show only tool calls and results
    cost   - Show token usage and cost summary
"""

import json
import sys
import argparse


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


def main():
    parser = argparse.ArgumentParser(description="Parse OpenCode JSON output")
    parser.add_argument(
        "--mode",
        choices=["text", "full", "tools", "cost"],
        default="text",
        help="Output mode (default: text)",
    )
    args = parser.parse_args()

    lines = sys.stdin.readlines()
    events = parse_events(lines)

    if not events:
        print("(no output received from OpenCode)", file=sys.stderr)
        sys.exit(1)

    if args.mode == "text":
        print(extract_text(events))
    elif args.mode == "full":
        print(extract_full(events))
    elif args.mode == "tools":
        print(extract_tools(events))
    elif args.mode == "cost":
        print(extract_cost(events))


if __name__ == "__main__":
    main()
