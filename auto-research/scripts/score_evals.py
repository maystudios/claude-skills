#!/usr/bin/env python3
"""
Deterministic scorer for the auto-research eval loop.

Reads:
  - evals.json  : test prompts + binary assertions
  - outputs/    : one Markdown file per test prompt (named eval-<id>.md)

For each (output, assertion) pair, decides pass/fail based on a small
vocabulary of pattern types. Writes score.json next to the outputs dir
and prints a one-line summary to stdout.

The vocabulary is intentionally narrow. If an assertion does not parse,
the scorer raises an error rather than silently passing or failing — this
forces evals.json to stay honest.

Usage:
  python score_evals.py --evals path/to/evals.json --outputs path/to/iteration-N/outputs/
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable


# ---------- Predicate library ----------------------------------------------

def _wc(text: str) -> int:
    return len(text.split())


def _line(text: str, which: str) -> str:
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return ""
    return lines[0] if which == "first" else lines[-1]


def _q(s: str) -> str:
    """Strip surrounding single or double quotes / backticks."""
    s = s.strip()
    for pair in ("''", '""', "``"):
        if len(s) >= 2 and s[0] == pair[0] and s[-1] == pair[1]:
            return s[1:-1]
    return s


def _build(assertion_text: str) -> Callable[[str], bool]:
    """
    Map a natural-language assertion to a predicate function.

    Supported patterns (case-insensitive on the directive, case-sensitive on the value):
      contains the substring '<X>'
      does NOT contain '<X>' / does not contain '<X>'
      matches the regex `<X>` / matches regex `<X>`
      does NOT match the regex `<X>`
      is under <N> words / is over <N> words
      is between <N> and <M> words
      contains at least <N> occurrences of '<X>'
      starts with '<X>' / ends with '<X>'
      first line <predicate>  /  last line <predicate>
    """
    a = assertion_text.strip()

    # first line / last line wrappers
    m = re.match(r"^(?P<which>first|last) line\s+(?P<rest>.+)$", a, re.IGNORECASE)
    if m:
        which = m.group("which").lower()
        inner = _build(m.group("rest"))
        return lambda text: inner(_line(text, which))

    # contains substring
    m = re.match(r"^contains the substring\s+(?P<v>.+)$", a, re.IGNORECASE)
    if m:
        needle = _q(m.group("v"))
        return lambda text: needle in text

    # does NOT contain
    m = re.match(r"^does not contain\s+(?P<v>.+)$", a, re.IGNORECASE)
    if m:
        needle = _q(m.group("v"))
        return lambda text: needle not in text

    # matches the regex
    m = re.match(r"^matches (?:the )?regex\s+(?P<v>.+)$", a, re.IGNORECASE)
    if m:
        pat = re.compile(_q(m.group("v")), re.MULTILINE | re.DOTALL)
        return lambda text: bool(pat.search(text))

    # does NOT match the regex
    m = re.match(r"^does not match (?:the )?regex\s+(?P<v>.+)$", a, re.IGNORECASE)
    if m:
        pat = re.compile(_q(m.group("v")), re.MULTILINE | re.DOTALL)
        return lambda text: not pat.search(text)

    # is under N words
    m = re.match(r"^is under (?P<n>\d+) words?$", a, re.IGNORECASE)
    if m:
        n = int(m.group("n"))
        return lambda text: _wc(text) < n

    # is over N words
    m = re.match(r"^is over (?P<n>\d+) words?$", a, re.IGNORECASE)
    if m:
        n = int(m.group("n"))
        return lambda text: _wc(text) > n

    # is between N and M words
    m = re.match(r"^is between (?P<n>\d+) and (?P<m>\d+) words?$", a, re.IGNORECASE)
    if m:
        n, m_ = int(m.group("n")), int(m.group("m"))
        return lambda text: n <= _wc(text) <= m_

    # contains at least N occurrences of '<X>'
    m = re.match(r"^contains at least (?P<n>\d+) occurrences? of\s+(?P<v>.+)$", a, re.IGNORECASE)
    if m:
        n = int(m.group("n"))
        needle = _q(m.group("v"))
        return lambda text: text.count(needle) >= n

    # starts with
    m = re.match(r"^starts with\s+(?P<v>.+)$", a, re.IGNORECASE)
    if m:
        needle = _q(m.group("v"))
        return lambda text: text.lstrip().startswith(needle)

    # ends with
    m = re.match(r"^ends with\s+(?P<v>.+)$", a, re.IGNORECASE)
    if m:
        needle = _q(m.group("v"))
        return lambda text: text.rstrip().endswith(needle)

    raise ValueError(
        f"Unrecognized assertion pattern: {assertion_text!r}\n"
        "See references/eval-loop.md for the supported vocabulary."
    )


# ---------- Main scoring loop -----------------------------------------------

def score(evals_path: Path, outputs_dir: Path) -> dict:
    spec = json.loads(evals_path.read_text(encoding="utf-8"))
    prompts = spec["test_prompts"]
    assertions = spec["assertions"]

    # Compile once
    compiled = []
    for assertion in assertions:
        try:
            fn = _build(assertion["text"])
        except ValueError as e:
            raise SystemExit(f"[evals.json invalid] {e}")
        compiled.append((assertion["id"], assertion["text"], fn))

    results = []
    total_pass = 0
    total = 0

    for prompt in prompts:
        out_path = outputs_dir / f"eval-{prompt['id']}.md"
        if not out_path.exists():
            print(f"[warn] missing output: {out_path}", file=sys.stderr)
            text = ""
        else:
            text = out_path.read_text(encoding="utf-8", errors="replace")

        per_assertion = []
        for aid, atext, fn in compiled:
            try:
                ok = bool(fn(text))
            except Exception as e:
                ok = False
                per_assertion.append({"id": aid, "text": atext, "pass": ok,
                                      "error": str(e)})
                total += 1
                continue
            per_assertion.append({"id": aid, "text": atext, "pass": ok})
            total_pass += int(ok)
            total += 1

        results.append({"prompt_id": prompt["id"], "assertions": per_assertion})

    pass_rate = total_pass / total if total else 0.0
    summary = {
        "pass_rate": pass_rate,
        "passed": total_pass,
        "total": total,
        "results": results,
    }

    score_path = outputs_dir / "score.json"
    score_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"pass_rate={pass_rate:.4f} ({total_pass}/{total}) → {score_path}")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evals", required=True, type=Path)
    ap.add_argument("--outputs", required=True, type=Path)
    args = ap.parse_args()

    if not args.evals.exists():
        print(f"evals.json not found: {args.evals}", file=sys.stderr)
        return 2
    if not args.outputs.exists() or not args.outputs.is_dir():
        print(f"outputs dir not found: {args.outputs}", file=sys.stderr)
        return 2

    score(args.evals, args.outputs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
