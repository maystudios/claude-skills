#!/usr/bin/env python3
"""Autoresearch-style test harness for the opencode skill.

Tests the skill by running real OpenCode invocations against multiple models
and scoring the results. Outputs a TSV results log.

Usage:
    python test_skill.py                    # Run all tests with all models
    python test_skill.py --model openai/gpt-5.3-codex  # Single model
    python test_skill.py --test review      # Single test category
    python test_skill.py --quick            # Fast subset only
    python test_skill.py --loop             # Autoresearch loop: keep running until interrupted
    python test_skill.py --loop --max-iter 5  # Loop with max iterations
    python test_skill.py --pipeline         # Test implement-then-review pipeline
    python test_skill.py --compare          # Parallel multi-model comparison
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
PARSE_SCRIPT = SKILL_DIR / "scripts" / "parse_output.py"

MODELS = [
    "openai/gpt-5.3-codex",
    "openai/gpt-5.4",
]

# Cross-model pairings for pipeline tests
PIPELINE_PAIRS = [
    ("openai/gpt-5.4", "openai/gpt-5.3-codex"),
    ("openai/gpt-5.3-codex", "openai/gpt-5.4"),
]

# Fallback chain for error recovery
FALLBACK_CHAIN = [
    "openai/gpt-5.4",
    "openai/gpt-5.3-codex",
    "openai/gpt-5.4-mini-fast",
    "github-copilot/gpt-5.4",
]

TIMEOUT = 300  # seconds per test (5 min)

# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

TEST_CASES = {
    "review": {
        "description": "Code review of a real project file",
        "agent": "plan",
        "prompt": (
            "[CONTEXT]\n"
            "Unreal Engine 5.7 C++ project (VHS) using GAS.\n\n"
            "[TASK]\n"
            "Review Source/VHS/AbilitySystem/VHSAbilitySystemComponent.h and .cpp for: "
            "correctness, potential bugs, performance issues, memory leaks, UE5 best practices.\n\n"
            "[SCOPE]\n"
            "Review ONLY the AbilitySystemComponent files. Do NOT explore other directories.\n\n"
            "[OUTPUT FORMAT]\n"
            "For each issue: [SEVERITY] File:Line -- Issue -- Fix. Keep under 300 words."
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
            "[CONTEXT]\n"
            "Unreal Engine 5.7 C++ project (VHS - horror game).\n\n"
            "[TASK]\n"
            "Answer these questions:\n"
            "1. What GAS components are implemented?\n"
            "2. How is the AbilitySystemComponent initialized?\n"
            "3. What gameplay abilities exist?\n\n"
            "[SCOPE]\n"
            "Search ONLY in Source/VHS/. Do NOT explore Engine or Plugin directories.\n\n"
            "[OUTPUT FORMAT]\n"
            "Cite file paths for every claim. Keep under 300 words."
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
            "[CONTEXT]\n"
            "UE5.7 project (VHS) using GAS for sprint and stamina.\n\n"
            "[BUG REPORT]\n"
            "Sprint ability GA_Sprint drains stamina but recovery doesn't start after sprint stops. "
            "Recovery is a gameplay effect with MMC.\n\n"
            "[TASK]\n"
            "Investigate root cause. Check: effect removal timing, MMC dependencies, "
            "tag blocking on recovery effect, attribute clamping.\n\n"
            "[SCOPE]\n"
            "Check ONLY the AbilitySystem/ directory. Do NOT explore other directories.\n\n"
            "[OUTPUT FORMAT]\n"
            "1. Root cause (most likely)\n2. Evidence (file:line)\n3. Fix. Keep under 200 words."
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
    "hard_review": {
        "description": "Deep cross-file architecture review (hard)",
        "agent": "plan",
        "prompt": (
            "[CONTEXT]\n"
            "Unreal Engine 5.7 C++ project (VHS) using GAS, Enhanced Input, StateTree.\n\n"
            "[TASK]\n"
            "Architecture review of GAS integration across the codebase:\n"
            "1. How does the ASC connect to Character and PlayerState?\n"
            "2. Any GAS anti-patterns (ASC ownership, effect stacking, missing replication)?\n"
            "3. Is the interaction system properly integrated with GAS?\n\n"
            "[SCOPE]\n"
            "Read files in Source/VHS/. Do NOT explore Engine or Plugin directories.\n\n"
            "[OUTPUT FORMAT]\n"
            "For each finding: [SEVERITY] File:Line -- Issue -- Fix. Keep under 500 words."
        ),
        "files": [],
        "scoring": {
            "mentions_line_numbers": 2,
            "mentions_specific_issues": 3,
            "suggests_fixes": 2,
            "understands_ue5": 2,
            "response_not_empty": 1,
            "no_hallucinated_files": 1,
            "mentions_real_files": 2,
            "response_is_structured": 1,
        },
    },
    "hard_debug": {
        "description": "Complex multi-system bug diagnosis (hard)",
        "agent": "plan",
        "prompt": (
            "[CONTEXT]\n"
            "UE5.7 VHS horror game using GAS. Sprint uses GA_Sprint with stamina attributes. "
            "Interaction uses GA_Interact.\n\n"
            "[BUG REPORT]\n"
            "Player sometimes can't interact with objects after sprinting and running out of stamina.\n\n"
            "[TASK]\n"
            "Investigate how sprint and interaction systems conflict. Check:\n"
            "- Tag blocking between GA_Sprint and GA_Interact\n"
            "- Ability activation conditions and stamina thresholds\n"
            "- State machine issues and effect cleanup\n\n"
            "[SCOPE]\n"
            "Investigate Source/VHS/ directory.\n\n"
            "[OUTPUT FORMAT]\n"
            "1. Root cause\n2. Evidence (file:line)\n3. Fix. Keep under 500 words."
        ),
        "files": [],
        "scoring": {
            "response_not_empty": 1,
            "identifies_plausible_causes": 3,
            "references_gas_patterns": 2,
            "mentions_mmc_or_ge": 1,
            "suggests_investigation_steps": 2,
            "response_is_structured": 1,
            "mentions_real_files": 2,
        },
    },
    "scoped_implement": {
        "description": "Scoped implementation task (read-only validation)",
        "agent": "plan",
        "prompt": (
            "[CONTEXT]\n"
            "UE5.7 C++ project (VHS). GAS naming: GA_ (abilities), GC_ (cues), MMC_ (magnitude calcs).\n"
            "Headers and .cpp side-by-side, no Public/Private split. #pragma once, CoreMinimal.h first.\n\n"
            "[TASK]\n"
            "Design (do NOT implement) a new gameplay ability GA_Crouch that:\n"
            "- Reduces movement speed by 50% while active\n"
            "- Uses a gameplay effect GE_CrouchSlow for the speed modifier\n"
            "- Has a gameplay tag State.Crouching applied while active\n"
            "- Cannot activate during sprint (blocked by State.Sprinting tag)\n\n"
            "[SCOPE]\n"
            "Reference Source/VHS/AbilitySystem/Abilities/ for existing patterns.\n\n"
            "[OUTPUT FORMAT]\n"
            "Provide: 1. Header file content 2. Cpp file content 3. GameplayEffect setup. "
            "Follow existing GA_Sprint patterns."
        ),
        "files": [],
        "scoring": {
            "response_not_empty": 1,
            "mentions_real_files": 2,
            "references_gas_patterns": 3,
            "response_is_structured": 2,
            "suggests_fixes": 2,  # reusing: checks for concrete code suggestions
            "understands_ue5": 3,
        },
    },
}

# Pipeline test: implementation + cross-model review
PIPELINE_TESTS = {
    "pipeline_design_review": {
        "description": "Design with model A, review with model B",
        "implement_prompt": (
            "[CONTEXT]\n"
            "UE5.7 C++ project (VHS) using GAS.\n\n"
            "[TASK]\n"
            "Design a GA_Crouch gameplay ability following the GA_Sprint pattern in "
            "Source/VHS/AbilitySystem/Abilities/. Output the .h and .cpp content.\n\n"
            "[SCOPE]\n"
            "Read ONLY Source/VHS/AbilitySystem/Abilities/ for reference patterns.\n\n"
            "[OUTPUT FORMAT]\n"
            "Full .h and .cpp file contents ready to save."
        ),
        "review_prompt_template": (
            "[CONTEXT]\n"
            "UE5.7 C++ project (VHS) using GAS.\n\n"
            "[TASK]\n"
            "Review this GA_Crouch ability design for: GAS best practices, "
            "replication correctness, tag blocking, effect cleanup, memory safety.\n\n"
            "--- DESIGN TO REVIEW ---\n{design_output}\n--- END DESIGN ---\n\n"
            "[OUTPUT FORMAT]\n"
            "For each issue: [SEVERITY] -- Issue -- Fix. Keep under 300 words."
        ),
        "scoring": {
            "response_not_empty": 1,
            "mentions_specific_issues": 2,
            "references_gas_patterns": 3,
            "response_is_structured": 2,
            "understands_ue5": 2,
        },
    },
}

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_opencode(model, agent, prompt, files=None, timeout=TIMEOUT):
    """Run opencode and return (text_output, tokens, cost, duration, status)."""
    files = files or []
    opencode_bin = os.environ.get("OPENCODE_BIN", "opencode")
    if sys.platform == "win32":
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
            total_tokens += tokens.get("input", 0) + tokens.get("output", 0) + tokens.get("reasoning", 0)
            total_cost += ev.get("part", {}).get("cost", 0)

    text = "".join(text_parts)
    status = "ok" if text else "empty"
    return text, total_tokens, total_cost, duration, status


def run_with_fallback(agent, prompt, files=None, timeout=TIMEOUT, preferred_model=None):
    """Run opencode with automatic model fallback on failure."""
    chain = [preferred_model] + FALLBACK_CHAIN if preferred_model else FALLBACK_CHAIN
    seen = set()
    for model in chain:
        if model in seen or model is None:
            continue
        seen.add(model)
        text, tokens, cost, duration, status = run_opencode(model, agent, prompt, files, timeout)
        if status == "ok":
            return text, tokens, cost, duration, status, model
        print(f"    [{model}] failed ({status}), trying fallback...")
    return "", 0, 0.0, 0, "all_failed", "none"


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
                       "should", "could", "potential", "risk", "vulnerability", "warning",
                       "concern", "note", "redundant", "unused", "unnecessary", "inefficient",
                       "unsafe", "deprecated", "anti-pattern", "smell"]
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
                    "unreal", "ue5", "actor", "component", "blueprint", "ustruct",
                    "generated.h", "coreminal", "replicated"]
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
                      "source/vhs", "ga_crouch", "horrorplayercontroller"]
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
                       "the issue", "the problem", "reason", "due to", "stems from",
                       "triggered by", "results in", "leads to", "prevents", "blocks",
                       "conflict", "race condition", "timing", "never"]
        hits = sum(1 for w in cause_words if w in text_lower)
        if hits >= 2:
            score += scoring["identifies_plausible_causes"]
            details["identifies_plausible_causes"] = f"PASS ({hits})"
        else:
            details["identifies_plausible_causes"] = f"FAIL ({hits})"

    if "references_gas_patterns" in scoring:
        gas_words = ["gameplay effect", "gameplay ability", "attribute", "modifier",
                     "ga_", "ge_", "mmc_", "gas", "gc_", "gameplay tag",
                     "ability system", "effect stack"]
        hits = sum(1 for w in gas_words if w in text_lower)
        if hits >= 2:
            score += scoring["references_gas_patterns"]
            details["references_gas_patterns"] = f"PASS ({hits})"
        else:
            details["references_gas_patterns"] = f"FAIL ({hits})"

    if "mentions_mmc_or_ge" in scoring:
        if "mmc" in text_lower or "modifier magnitude" in text_lower or "gameplay effect" in text_lower or "ge_" in text_lower or "default effect" in text_lower or "effect stack" in text_lower:
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
# Runners
# ---------------------------------------------------------------------------


def run_standard_tests(models, tests, tsv):
    """Run standard single-model tests."""
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

            print(f"{score}/{max_score} ({pct}%) | {tokens:,} tok | ${cost:.4f} | {duration:.0f}s | {status}")
            for k, v in details.items():
                marker = "+" if "PASS" in str(v) else "-"
                print(f"    {marker} {k}: {v}")

            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            detail_str = "; ".join(f"{k}={v}" for k, v in details.items())
            tsv.write(f"{ts}\t{model}\tstandard/{test_name}\t{score}\t{max_score}\t{pct}\t{tokens}\t{cost:.4f}\t{duration:.0f}\t{status}\t{detail_str}\n")
            tsv.flush()

            results.append({
                "model": model, "test": test_name, "score": score,
                "max_score": max_score, "pct": pct, "status": status,
            })

    return total_score, total_max, results


def run_pipeline_tests(tsv):
    """Run implement-then-review pipeline tests with cross-model validation."""
    print(f"\n{'='*70}")
    print("PIPELINE TESTS (implement with model A, review with model B)")
    print(f"{'='*70}")

    total_score = 0
    total_max = 0
    results = []

    for test_name, test_case in PIPELINE_TESTS.items():
        for impl_model, review_model in PIPELINE_PAIRS:
            print(f"\n--- {test_name} | impl={impl_model} → review={review_model} ---")

            # Step 1: Implementation/Design
            print(f"  [1/2] Implementing with {impl_model}... ", end="", flush=True)
            impl_text, impl_tok, impl_cost, impl_dur, impl_status = run_opencode(
                model=impl_model,
                agent="plan",
                prompt=test_case["implement_prompt"],
            )

            if impl_status != "ok":
                print(f"FAIL ({impl_status})")
                score, max_score = 0, sum(test_case["scoring"].values())
                details = {"implement": f"FAIL ({impl_status})"}
                total_max += max_score

                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                detail_str = "; ".join(f"{k}={v}" for k, v in details.items())
                tsv.write(f"{ts}\t{impl_model}+{review_model}\tpipeline/{test_name}\t0\t{max_score}\t0\t{impl_tok}\t{impl_cost:.4f}\t{impl_dur:.0f}\timpl_{impl_status}\t{detail_str}\n")
                tsv.flush()
                continue

            print(f"OK ({impl_tok:,} tok, {impl_dur:.0f}s)")

            # Step 2: Cross-model review
            review_prompt = test_case["review_prompt_template"].format(
                design_output=impl_text[:3000]  # Cap to avoid context overflow
            )
            print(f"  [2/2] Reviewing with {review_model}... ", end="", flush=True)
            review_text, review_tok, review_cost, review_dur, review_status = run_opencode(
                model=review_model,
                agent="plan",
                prompt=review_prompt,
            )

            combined_text = review_text if review_status == "ok" else ""
            total_tokens = impl_tok + review_tok
            total_cost = impl_cost + review_cost
            total_duration = impl_dur + review_dur

            if review_status == "ok":
                score, max_score, details = score_response(combined_text, test_case)
                pct = round(score / max_score * 100) if max_score > 0 else 0
                details["pipeline_complete"] = "PASS"
            else:
                score, max_score, pct = 0, sum(test_case["scoring"].values()), 0
                details = {"review": f"FAIL ({review_status})"}

            total_score += score
            total_max += max_score

            print(f"{score}/{max_score} ({pct}%) | {total_tokens:,} tok | ${total_cost:.4f} | {total_duration:.0f}s")
            for k, v in details.items():
                marker = "+" if "PASS" in str(v) else "-"
                print(f"    {marker} {k}: {v}")

            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            detail_str = "; ".join(f"{k}={v}" for k, v in details.items())
            tsv.write(f"{ts}\t{impl_model}+{review_model}\tpipeline/{test_name}\t{score}\t{max_score}\t{pct}\t{total_tokens}\t{total_cost:.4f}\t{total_duration:.0f}\t{'ok' if review_status == 'ok' else review_status}\t{detail_str}\n")
            tsv.flush()

            results.append({
                "models": f"{impl_model}+{review_model}", "test": test_name,
                "score": score, "max_score": max_score, "pct": pct,
            })

    return total_score, total_max, results


def run_fallback_test(tsv):
    """Test automatic model fallback chain."""
    print(f"\n{'='*70}")
    print("FALLBACK TEST (automatic model recovery)")
    print(f"{'='*70}")

    prompt = (
        "[CONTEXT]\nUE5.7 C++ project.\n\n"
        "[TASK]\nList the files in Source/VHS/AbilitySystem/. Keep under 100 words.\n\n"
        "[SCOPE]\nONLY Source/VHS/AbilitySystem/."
    )

    print(f"\n--- fallback_chain ---")
    text, tokens, cost, duration, status, used_model = run_with_fallback(
        agent="plan",
        prompt=prompt,
        preferred_model="openai/gpt-5.4",
    )

    print(f"  Result: {status} via {used_model} | {tokens:,} tok | {duration:.0f}s")

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    tsv.write(f"{ts}\t{used_model}\tfallback/chain_test\t{'1' if status == 'ok' else '0'}\t1\t{'100' if status == 'ok' else '0'}\t{tokens}\t{cost:.4f}\t{duration:.0f}\t{status}\tused_model={used_model}\n")
    tsv.flush()

    return (1 if status == "ok" else 0), 1


def run_loop(models, tests, tsv, max_iterations):
    """Autoresearch-style infinite improvement loop.

    Runs tests repeatedly, tracking best scores per model/test combination.
    Keeps running until interrupted or max_iterations reached.
    """
    print(f"\n{'='*70}")
    print(f"AUTORESEARCH LOOP MODE (max {max_iterations} iterations, Ctrl+C to stop)")
    print(f"{'='*70}")

    best_scores = {}  # (model, test) -> best pct
    iteration = 0

    try:
        while iteration < max_iterations:
            iteration += 1
            print(f"\n{'='*70}")
            print(f"ITERATION {iteration}/{max_iterations}")
            print(f"{'='*70}")

            iter_score = 0
            iter_max = 0

            for test_name, test_case in tests.items():
                for model in models:
                    key = (model, test_name)
                    print(f"\n--- [{iteration}] {test_name} | {model} ---")
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

                    iter_score += score
                    iter_max += max_score

                    # Track best score (autoresearch ratchet pattern)
                    prev_best = best_scores.get(key, 0)
                    improved = pct > prev_best
                    if improved:
                        best_scores[key] = pct

                    marker = "^" if improved else "=" if pct == prev_best else "v"
                    print(f"{score}/{max_score} ({pct}%) [{marker} best={best_scores.get(key, pct)}%] | {tokens:,} tok | {duration:.0f}s")

                    ts = time.strftime("%Y-%m-%d %H:%M:%S")
                    detail_str = "; ".join(f"{k}={v}" for k, v in details.items())
                    tsv.write(f"{ts}\t{model}\tloop[{iteration}]/{test_name}\t{score}\t{max_score}\t{pct}\t{tokens}\t{cost:.4f}\t{duration:.0f}\t{status}\t{detail_str}\n")
                    tsv.flush()

            iter_pct = round(iter_score / iter_max * 100) if iter_max > 0 else 0
            print(f"\n  Iteration {iteration} total: {iter_score}/{iter_max} ({iter_pct}%)")

            # Early stop if all tests are at 100%
            if all(v == 100 for v in best_scores.values()) and len(best_scores) == len(tests) * len(models):
                print(f"\n  All tests at 100% -- stopping early.")
                break

    except KeyboardInterrupt:
        print(f"\n\n  Loop interrupted by user after {iteration} iterations.")

    print(f"\n{'='*70}")
    print(f"LOOP SUMMARY (best scores across {iteration} iterations):")
    for (model, test), best_pct in sorted(best_scores.items()):
        print(f"  {model} / {test}: {best_pct}%")
    print(f"{'='*70}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Test the opencode skill")
    parser.add_argument("--model", type=str, help="Test only this model")
    parser.add_argument("--test", type=str, help="Run only this test category")
    parser.add_argument("--quick", action="store_true", help="Fast subset (research only, fast models)")
    parser.add_argument("--pipeline", action="store_true", help="Run pipeline tests (cross-model implement+review)")
    parser.add_argument("--compare", action="store_true", help="Run all models on all tests for comparison")
    parser.add_argument("--fallback", action="store_true", help="Test model fallback chain")
    parser.add_argument("--loop", action="store_true", help="Autoresearch loop mode: run repeatedly")
    parser.add_argument("--max-iter", type=int, default=10, help="Max iterations for loop mode (default: 10)")
    parser.add_argument("--all", action="store_true", help="Run everything: standard + pipeline + fallback")
    args = parser.parse_args()

    models = [args.model] if args.model else MODELS
    tests = {args.test: TEST_CASES[args.test]} if args.test else TEST_CASES

    if args.quick:
        models = ["openai/gpt-5.4-mini-fast"]
        tests = {"research": TEST_CASES["research"]}

    if args.compare:
        models = ["openai/gpt-5.4", "openai/gpt-5.3-codex", "github-copilot/gpt-5.4"]

    # Header
    print(f"{'='*70}")
    print(f"OpenCode Skill Test Harness (autoresearch-style)")
    print(f"Models: {', '.join(models)}")
    print(f"Tests:  {', '.join(tests.keys())}")
    if args.pipeline:
        print(f"Pipeline pairs: {', '.join(f'{a}+{b}' for a, b in PIPELINE_PAIRS)}")
    if args.loop:
        print(f"Loop mode: max {args.max_iter} iterations")
    print(f"{'='*70}")

    # TSV log
    write_header = not RESULTS_FILE.exists()
    tsv = open(RESULTS_FILE, "a", encoding="utf-8")
    if write_header:
        tsv.write("timestamp\tmodel\ttest\tscore\tmax_score\tpercent\ttokens\tcost\tduration\tstatus\tdetails\n")

    total_score = 0
    total_max = 0

    # Loop mode
    if args.loop:
        run_loop(models, tests, tsv, args.max_iter)
        tsv.close()
        return 100  # Loop mode doesn't have a single score

    # Standard tests
    if not args.pipeline or args.all:
        std_score, std_max, _ = run_standard_tests(models, tests, tsv)
        total_score += std_score
        total_max += std_max

    # Pipeline tests
    if args.pipeline or args.all:
        pipe_score, pipe_max, _ = run_pipeline_tests(tsv)
        total_score += pipe_score
        total_max += pipe_max

    # Fallback test
    if args.fallback or args.all:
        fb_score, fb_max = run_fallback_test(tsv)
        total_score += fb_score
        total_max += fb_max

    tsv.close()

    # Summary
    total_pct = round(total_score / total_max * 100) if total_max > 0 else 0
    print(f"\n{'='*70}")
    print(f"TOTAL: {total_score}/{total_max} ({total_pct}%)")
    print(f"Results appended to: {RESULTS_FILE}")
    print(f"{'='*70}")

    return total_pct


if __name__ == "__main__":
    sys.exit(0 if main() >= 50 else 1)
