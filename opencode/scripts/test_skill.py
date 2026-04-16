#!/usr/bin/env python3
"""Autoresearch-style test harness for the opencode skill.

Tests the skill by running real OpenCode invocations against multiple models
and scoring the results. Outputs a TSV results log.

Usage:
    python test_skill.py                    # Run all tests with all models
    python test_skill.py --model openai/gpt-5.3-codex  # Single model
    python test_skill.py --test review      # Single test category
    python test_skill.py --quick            # Fast subset only
"""

import json
import subprocess
import sys
import os
import time
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_DIR = "C:/UnrealEngine/VHS"
SKILL_DIR = Path(__file__).parent.parent
RESULTS_FILE = SKILL_DIR / "results.tsv"

MODELS = [
    "openai/gpt-5.3-codex",
    "openai/gpt-5.4",
]

TIMEOUT = 180  # seconds per test

# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

TEST_CASES = {
    "review": {
        "description": "Code review of a real project file",
        "agent": "plan",
        "prompt": (
            "Read and review the file Source/VHS/AbilitySystem/VHSAbilitySystemComponent.h "
            "and VHSAbilitySystemComponent.cpp for: correctness, potential bugs, "
            "performance issues, memory leaks, and UE5 best practices. "
            "Be specific about line numbers and suggest concrete fixes. "
            "Focus on GAS patterns. Keep response under 300 words."
        ),
        "files": [],
        "scoring": {
            "mentions_line_numbers": 2,
            "mentions_specific_issues": 3,
            "suggests_fixes": 3,
            "understands_ue5": 2,
            "response_not_empty": 1,
            "no_hallucinated_files": 1,
        },
    },
    "research": {
        "description": "Codebase architecture exploration",
        "agent": "plan",
        "prompt": (
            "Explore this Unreal Engine 5 project and answer: "
            "1. What GAS components are implemented? "
            "2. How is the AbilitySystemComponent initialized? "
            "3. What gameplay abilities exist? "
            "Keep your response under 300 words. Be factual, cite file paths."
        ),
        "files": [],
        "scoring": {
            "mentions_real_files": 3,
            "answers_all_questions": 3,
            "cites_specific_code": 2,
            "no_hallucinations": 2,
            "response_not_empty": 1,
        },
    },
    "debug": {
        "description": "Diagnose a hypothetical bug",
        "agent": "plan",
        "prompt": (
            "Debug this issue: sprint ability GA_Sprint drains stamina but recovery doesnt start "
            "after sprint stops. The recovery is a gameplay effect with MMC. "
            "Check ONLY the AbilitySystem/ directory. Do NOT explore other directories. "
            "Identify root causes with specific file paths and line numbers. "
            "Keep response under 200 words."
        ),
        "files": [],
        "scoring": {
            "identifies_plausible_causes": 3,
            "references_gas_patterns": 2,
            "mentions_mmc_or_ge": 2,
            "suggests_investigation_steps": 2,
            "response_not_empty": 1,
            "response_is_structured": 1,
        },
    },
}

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_opencode(model, agent, prompt, files, timeout=TIMEOUT):
    """Run opencode and return (text_output, tokens, cost, duration, status)."""
    # On Windows, opencode is a .cmd script - need full path or shell=True
    opencode_bin = os.environ.get("OPENCODE_BIN", "opencode")
    if sys.platform == "win32":
        # Try to find .cmd version
        import shutil
        found = shutil.which("opencode")
        if found:
            opencode_bin = found

    cmd = [
        opencode_bin, "run",
        "--format", "json",
        "--model", model,
        "--agent", agent,
        "--dir", PROJECT_DIR,
        "--dangerously-skip-permissions",
    ]
    for f in files:
        cmd.extend(["-f", os.path.join(PROJECT_DIR, f)])
    cmd.append(prompt)

    env = os.environ.copy()
    env["OPENCODE_DISABLE_AUTOUPDATE"] = "true"
    env["PYTHONIOENCODING"] = "utf-8"

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            env=env,
            shell=(sys.platform == "win32"),
        )
        duration = time.time() - start
        stdout = result.stdout.decode("utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return "", 0, 0.0, timeout, "timeout"
    except FileNotFoundError:
        return "opencode not found in PATH", 0, 0.0, 0, "crash"
    except Exception as e:
        return str(e), 0, 0.0, time.time() - start, "crash"

    if result.returncode != 0 and not stdout.strip():
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        return f"exit code {result.returncode}: {stderr[:500]}", 0, 0.0, duration, "crash"

    # Parse ndjson
    text_parts = []
    total_tokens = 0
    total_cost = 0.0
    tool_calls = 0

    for line in stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue

        if ev.get("type") == "text":
            t = ev.get("part", {}).get("text", "")
            if t:
                text_parts.append(t)
        elif ev.get("type") == "tool_call":
            tool_calls += 1
        elif ev.get("type") == "step_finish":
            tokens = ev.get("part", {}).get("tokens", {})
            total_tokens += tokens.get("input", 0) + tokens.get("output", 0)
            total_cost += ev.get("part", {}).get("cost", 0)

    text = "".join(text_parts)
    status = "ok" if text else "empty"
    return text, total_tokens, total_cost, duration, status


# ---------------------------------------------------------------------------
# Scorer
# ---------------------------------------------------------------------------


def score_response(text, test_case):
    """Score a response based on test case criteria. Returns (score, max_score, details)."""
    scoring = test_case["scoring"]
    max_score = sum(scoring.values())
    score = 0
    details = {}

    text_lower = text.lower()

    # Generic checks
    if "response_not_empty" in scoring and len(text.strip()) > 50:
        score += scoring["response_not_empty"]
        details["response_not_empty"] = "PASS"
    elif "response_not_empty" in scoring:
        details["response_not_empty"] = "FAIL"

    if "no_hallucinated_files" in scoring:
        fake_markers = ["src/main.cpp", "app.js", "index.ts", "main.py"]
        if not any(m in text_lower for m in fake_markers):
            score += scoring["no_hallucinated_files"]
            details["no_hallucinated_files"] = "PASS"
        else:
            details["no_hallucinated_files"] = "FAIL"

    if "no_hallucinations" in scoring:
        fake_markers = ["src/main.cpp", "app.js", "index.ts", "main.py", "package.json"]
        if not any(m in text_lower for m in fake_markers):
            score += scoring["no_hallucinations"]
            details["no_hallucinations"] = "PASS"
        else:
            details["no_hallucinations"] = "FAIL"

    # Review-specific
    if "mentions_line_numbers" in scoring:
        import re
        if re.search(r"line\s*\d+|:\d+|L\d+", text):
            score += scoring["mentions_line_numbers"]
            details["mentions_line_numbers"] = "PASS"
        else:
            details["mentions_line_numbers"] = "FAIL"

    if "mentions_specific_issues" in scoring:
        issue_words = ["bug", "issue", "problem", "error", "missing", "incorrect",
                       "should", "could", "potential", "risk", "vulnerability", "warning"]
        hits = sum(1 for w in issue_words if w in text_lower)
        if hits >= 3:
            score += scoring["mentions_specific_issues"]
            details["mentions_specific_issues"] = f"PASS ({hits} markers)"
        else:
            details["mentions_specific_issues"] = f"FAIL ({hits} markers)"

    if "suggests_fixes" in scoring:
        fix_words = ["fix", "change", "replace", "add", "remove", "instead", "suggest",
                     "recommend", "consider", "should be", "use"]
        hits = sum(1 for w in fix_words if w in text_lower)
        if hits >= 3:
            score += scoring["suggests_fixes"]
            details["suggests_fixes"] = f"PASS ({hits} markers)"
        else:
            details["suggests_fixes"] = f"FAIL ({hits} markers)"

    if "understands_ue5" in scoring:
        ue_words = ["uproperty", "ufunction", "uclass", "gas", "gameplay", "ability",
                    "unreal", "ue5", "actor", "component", "blueprint"]
        hits = sum(1 for w in ue_words if w in text_lower)
        if hits >= 2:
            score += scoring["understands_ue5"]
            details["understands_ue5"] = f"PASS ({hits} markers)"
        else:
            details["understands_ue5"] = f"FAIL ({hits} markers)"

    # Research-specific
    if "mentions_real_files" in scoring:
        real_paths = ["abilitysystem", "vhsabilitysystemcomponent", "horrorcharacter",
                      "ga_sprint", "ga_interact", "vhsattributeset", "vhsgameplaytags",
                      "source/vhs"]
        hits = sum(1 for p in real_paths if p in text_lower)
        if hits >= 2:
            score += scoring["mentions_real_files"]
            details["mentions_real_files"] = f"PASS ({hits} paths)"
        else:
            details["mentions_real_files"] = f"FAIL ({hits} paths)"

    if "answers_all_questions" in scoring:
        markers = ["ability system component", "abilities", "gas"]
        if any("asc" in text_lower or "abilitysystemcomponent" in text_lower for _ in [1]):
            markers_hit = 1
        else:
            markers_hit = 0
        markers_hit += sum(1 for m in markers if m in text_lower)
        if markers_hit >= 2:
            score += scoring["answers_all_questions"]
            details["answers_all_questions"] = f"PASS ({markers_hit})"
        else:
            details["answers_all_questions"] = f"FAIL ({markers_hit})"

    if "cites_specific_code" in scoring:
        import re
        code_refs = len(re.findall(r'`[A-Z]\w+`|`\w+\.\w+`|```', text))
        if code_refs >= 2:
            score += scoring["cites_specific_code"]
            details["cites_specific_code"] = f"PASS ({code_refs} refs)"
        else:
            details["cites_specific_code"] = f"FAIL ({code_refs} refs)"

    # Debug-specific
    if "identifies_plausible_causes" in scoring:
        cause_words = ["cause", "because", "likely", "possibly", "root cause",
                       "the issue", "the problem", "reason"]
        hits = sum(1 for w in cause_words if w in text_lower)
        if hits >= 2:
            score += scoring["identifies_plausible_causes"]
            details["identifies_plausible_causes"] = f"PASS ({hits})"
        else:
            details["identifies_plausible_causes"] = f"FAIL ({hits})"

    if "references_gas_patterns" in scoring:
        gas_words = ["gameplay effect", "gameplay ability", "attribute", "modifier",
                     "ga_", "ge_", "mmc_", "gas"]
        hits = sum(1 for w in gas_words if w in text_lower)
        if hits >= 2:
            score += scoring["references_gas_patterns"]
            details["references_gas_patterns"] = f"PASS ({hits})"
        else:
            details["references_gas_patterns"] = f"FAIL ({hits})"

    if "mentions_mmc_or_ge" in scoring:
        if "mmc" in text_lower or "modifier magnitude" in text_lower or "gameplay effect" in text_lower:
            score += scoring["mentions_mmc_or_ge"]
            details["mentions_mmc_or_ge"] = "PASS"
        else:
            details["mentions_mmc_or_ge"] = "FAIL"

    if "suggests_investigation_steps" in scoring:
        step_words = ["check", "verify", "look at", "inspect", "debug", "set breakpoint",
                      "log", "print", "investigate", "examine", "step"]
        hits = sum(1 for w in step_words if w in text_lower)
        if hits >= 2:
            score += scoring["suggests_investigation_steps"]
            details["suggests_investigation_steps"] = f"PASS ({hits})"
        else:
            details["suggests_investigation_steps"] = f"FAIL ({hits})"

    if "response_is_structured" in scoring:
        structure_markers = ["1.", "2.", "##", "**", "- "]
        hits = sum(1 for m in structure_markers if m in text)
        if hits >= 2:
            score += scoring["response_is_structured"]
            details["response_is_structured"] = f"PASS ({hits})"
        else:
            details["response_is_structured"] = f"FAIL ({hits})"

    return score, max_score, details


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Test the opencode skill")
    parser.add_argument("--model", type=str, help="Test only this model")
    parser.add_argument("--test", type=str, help="Run only this test category")
    parser.add_argument("--quick", action="store_true", help="Fast subset (research only, fast models)")
    args = parser.parse_args()

    models = [args.model] if args.model else MODELS
    tests = {args.test: TEST_CASES[args.test]} if args.test else TEST_CASES

    if args.quick:
        models = ["openai/gpt-5.4-mini-fast"]
        tests = {"research": TEST_CASES["research"]}

    # Header
    print(f"{'='*70}")
    print(f"OpenCode Skill Test Harness (autoresearch-style)")
    print(f"Models: {', '.join(models)}")
    print(f"Tests:  {', '.join(tests.keys())}")
    print(f"{'='*70}")

    # TSV header
    write_header = not RESULTS_FILE.exists()
    tsv = open(RESULTS_FILE, "a", encoding="utf-8")
    if write_header:
        tsv.write("timestamp\tmodel\ttest\tscore\tmax_score\tpercent\ttokens\tcost\tduration\tstatus\tdetails\n")

    total_score = 0
    total_max = 0
    results = []

    for test_name, test_case in tests.items():
        for model in models:
            print(f"\n--- {test_name} | {model} ---")
            print(f"  Running... ", end="", flush=True)

            text, tokens, cost, duration, status = run_opencode(
                model=model,
                agent=test_case["agent"],
                prompt=test_case["prompt"],
                files=test_case.get("files", []),
            )

            if status == "ok":
                score, max_score, details = score_response(text, test_case)
                pct = round(score / max_score * 100) if max_score > 0 else 0
            else:
                score, max_score, pct = 0, sum(test_case["scoring"].values()), 0
                details = {status: "FAIL"}

            total_score += score
            total_max += max_score

            # Print result
            print(f"{score}/{max_score} ({pct}%) | {tokens:,} tok | ${cost:.4f} | {duration:.0f}s | {status}")
            for k, v in details.items():
                marker = "+" if "PASS" in str(v) else "-"
                print(f"    {marker} {k}: {v}")

            # Log to TSV
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            detail_str = "; ".join(f"{k}={v}" for k, v in details.items())
            tsv.write(f"{ts}\t{model}\t{test_name}\t{score}\t{max_score}\t{pct}\t{tokens}\t{cost:.4f}\t{duration:.0f}\t{status}\t{detail_str}\n")
            tsv.flush()

            results.append({
                "model": model, "test": test_name, "score": score,
                "max_score": max_score, "pct": pct, "status": status,
            })

    tsv.close()

    # Summary
    total_pct = round(total_score / total_max * 100) if total_max > 0 else 0
    print(f"\n{'='*70}")
    print(f"TOTAL: {total_score}/{total_max} ({total_pct}%)")
    print(f"Results appended to: {RESULTS_FILE}")
    print(f"{'='*70}")

    # Return score for the autoresearch loop
    return total_pct


if __name__ == "__main__":
    sys.exit(0 if main() >= 50 else 1)
