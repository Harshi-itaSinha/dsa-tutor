#!/usr/bin/env python3
"""
run_tests.py — Compile a C++ solution and run it against _tests.txt test cases.

Usage:
  python3 scripts/run_tests.py sessions/2026-04-05_Google/p1_two_sum.cpp
  python3 scripts/run_tests.py sessions/2026-04-05_Google/   # run all .cpp in dir
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# ── configuration ──────────────────────────────────────────────────────────────
TLE_SECONDS = 2          # seconds before a test case is killed as TLE
MEMORY_LIMIT_MB = 512    # memory cap for the compiled binary
CPP_STD = "c++17"
CPP_FLAGS = ["-O2", f"-std={CPP_STD}", "-Wall", "-Wno-unused-result"]


# ── colours (disabled if not a tty) ───────────────────────────────────────────
USE_COLOR = sys.stdout.isatty()

def green(s):  return f"\033[32m{s}\033[0m" if USE_COLOR else s
def red(s):    return f"\033[31m{s}\033[0m" if USE_COLOR else s
def yellow(s): return f"\033[33m{s}\033[0m" if USE_COLOR else s
def bold(s):   return f"\033[1m{s}\033[0m" if USE_COLOR else s


# ── test-case parsing ─────────────────────────────────────────────────────────

def parse_tests(test_file: Path) -> list[dict]:
    """Parse a _tests.txt file into a list of test dicts."""
    text = test_file.read_text()
    # split on ---TEST N--- markers
    blocks = re.split(r"---TEST\s+\d+---[^\n]*\n", text)
    headers = re.findall(r"---TEST\s+(\d+)---([^\n]*)\n", text)

    tests = []
    for (num, label), block in zip(headers, blocks[1:]):
        block = block.strip()
        # skip if only comments
        if not block or all(line.startswith("#") for line in block.splitlines()):
            continue

        flags = set()
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("# UNORDERED"):   flags.add("unordered")
            elif stripped.startswith("# FLOAT"):     flags.add("float")
            elif stripped.startswith("# DRIVER"):    flags.add("driver")
            elif stripped.startswith("# INTERACTIVE"):flags.add("interactive")

        # split INPUT / EXPECTED
        inp_match = re.search(r"INPUT\s*\n(.*?)(?=EXPECTED|\Z)", block, re.DOTALL)
        exp_match = re.search(r"EXPECTED\s*\n(.*?)(?=---TEST|\Z)", block, re.DOTALL)

        if not inp_match or not exp_match:
            print(yellow(f"  [WARN] TEST {num}: could not parse INPUT/EXPECTED blocks — skipping"))
            continue

        # strip comment lines from input/expected
        def strip_comments(text):
            lines = [l for l in text.splitlines() if not l.strip().startswith("#")]
            return "\n".join(lines).strip()

        tests.append({
            "num":      num,
            "label":    label.strip(),
            "input":    strip_comments(inp_match.group(1)),
            "expected": strip_comments(exp_match.group(1)),
            "flags":    flags,
        })

    return tests


# ── compilation ───────────────────────────────────────────────────────────────

def compile_cpp(source: Path) -> tuple[bool, str, Path]:
    """Compile C++ file. Returns (success, error_message, binary_path)."""
    binary = Path(tempfile.gettempdir()) / f"dsa_runner_{source.stem}"
    cmd = ["g++"] + CPP_FLAGS + [str(source), "-o", str(binary)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr, binary
    return True, "", binary


# ── test execution ─────────────────────────────────────────────────────────────

def run_test(binary: Path, test: dict) -> dict:
    """Run a single test. Returns result dict."""
    if "interactive" in test["flags"]:
        return {"status": "SKIP", "reason": "interactive problem — manual testing required"}
    if "driver" in test["flags"]:
        return {"status": "SKIP", "reason": "class driver needed — manual testing required"}

    # build command with memory limit (macOS: no ulimit -v in subprocess easily, use rlimit)
    cmd = [str(binary)]

    try:
        proc = subprocess.run(
            cmd,
            input=test["input"],
            capture_output=True,
            text=True,
            timeout=TLE_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {"status": "TLE", "actual": None}

    actual = proc.stdout.strip()
    expected = test["expected"].strip()

    if compare_output(actual, expected, test["flags"]):
        return {"status": "PASS", "actual": actual, "time": None}
    else:
        return {"status": "FAIL", "actual": actual, "expected": expected}


def compare_output(actual: str, expected: str, flags: set) -> bool:
    if "unordered" in flags:
        return sorted(actual.splitlines()) == sorted(expected.splitlines())
    if "float" in flags:
        try:
            a_vals = list(map(float, actual.split()))
            e_vals = list(map(float, expected.split()))
            return len(a_vals) == len(e_vals) and all(abs(a - e) < 1e-6 for a, e in zip(a_vals, e_vals))
        except ValueError:
            pass
    return actual == expected


# ── reporting ─────────────────────────────────────────────────────────────────

def run_all_tests(source: Path) -> tuple[int, int, list]:
    """Run all tests for a source file. Returns (passed, total, results)."""
    test_file = source.parent / (source.stem + "_tests.txt")
    if not test_file.exists():
        print(yellow(f"  No test file found: {test_file}"))
        return 0, 0, []

    print(f"\n{bold('Compiling:')} {source.name}")
    ok, err, binary = compile_cpp(source)
    if not ok:
        print(red("  COMPILE ERROR:"))
        for line in err.splitlines():
            print(f"    {line}")
        return 0, 0, []
    print(green("  Compiled OK"))

    tests = parse_tests(test_file)
    if not tests:
        print(yellow("  No parseable tests found in test file."))
        return 0, 0, []

    passed = 0
    results = []
    for test in tests:
        result = run_test(binary, test)
        result["num"] = test["num"]
        result["label"] = test["label"]
        result["input"] = test["input"]
        results.append(result)

        status = result["status"]
        label_str = f"TEST {test['num']}" + (f" ({test['label']})" if test["label"] else "")

        if status == "PASS":
            print(green(f"  ✓ {label_str}"))
            passed += 1
        elif status == "FAIL":
            print(red(f"  ✗ {label_str}"))
            print(f"      Input:    {test['input']!r}")
            print(f"      Expected: {result['expected']!r}")
            print(f"      Got:      {result['actual']!r}")
        elif status == "TLE":
            print(yellow(f"  ⏱ {label_str} — TLE (exceeded {TLE_SECONDS}s)"))
        elif status == "SKIP":
            print(yellow(f"  ↷ {label_str} — SKIPPED: {result['reason']}"))

    total = len(tests)
    bar = "─" * 50
    print(f"\n  {bar}")
    summary = f"  {passed}/{total} passed"
    if passed == total:
        print(green(bold(summary + " ✓ All tests pass!")))
    else:
        failed = [r for r in results if r["status"] == "FAIL"]
        tles   = [r for r in results if r["status"] == "TLE"]
        detail = []
        if failed: detail.append(f"{len(failed)} failed: tests {', '.join(r['num'] for r in failed)}")
        if tles:   detail.append(f"{len(tles)} TLE: tests {', '.join(r['num'] for r in tles)}")
        print(red(summary) + " | " + "; ".join(detail))

    # clean up binary
    try:
        binary.unlink()
    except Exception:
        pass

    return passed, total, results


def append_results_to_readme(session_dir: Path, source: Path, passed: int, total: int):
    """Append test result row to session README.md."""
    readme = session_dir / "README.md"
    if not readme.exists():
        return
    content = readme.read_text()
    status_str = "✓ All pass" if passed == total else f"✗ {total - passed} failing"
    row = f"| {source.name} | {passed} | {total} | {status_str} |"
    # append row if not already present
    if source.name not in content:
        content += "\n" + row
        readme.write_text(content)


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run test cases for a C++ DSA solution.")
    parser.add_argument("target", help="Path to a .cpp file or a session directory")
    args = parser.parse_args()

    target = Path(args.target)

    if target.is_dir():
        sources = sorted(target.glob("p*.cpp"))
        if not sources:
            print("No p*.cpp files found in directory.")
            sys.exit(1)
        total_passed = total_run = 0
        for src in sources:
            p, t, _ = run_all_tests(src)
            total_passed += p
            total_run += t
            if t > 0:
                append_results_to_readme(target, src, p, t)
        print(f"\n{bold('Session total:')} {total_passed}/{total_run} tests passed")
    elif target.suffix == ".cpp":
        p, t, _ = run_all_tests(target)
        if t > 0:
            append_results_to_readme(target.parent, target, p, t)
    else:
        print("Provide a .cpp file or a session directory.")
        sys.exit(1)


if __name__ == "__main__":
    main()
