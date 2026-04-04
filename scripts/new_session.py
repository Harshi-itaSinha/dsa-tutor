#!/usr/bin/env python3
"""
new_session.py — Bootstrap a new DSA session directory.

Usage:
  python3 scripts/new_session.py --type contest --company Google
  python3 scripts/new_session.py --type practice --topic dp
  python3 scripts/new_session.py --type doubt --topic "segment tree"
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
SESSIONS_DIR = ROOT / "sessions"
TEMPLATES_DIR = ROOT / "templates"
README_TEMPLATE = TEMPLATES_DIR / "session_readme.template"


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", s.lower().strip())
    return s.strip("_")


def make_session_dir(name: str) -> Path:
    """Create session directory, adding _2, _3 suffix if it already exists."""
    base = SESSIONS_DIR / name
    if not base.exists():
        base.mkdir(parents=True)
        return base
    for i in range(2, 20):
        candidate = SESSIONS_DIR / f"{name}_{i}"
        if not candidate.exists():
            candidate.mkdir(parents=True)
            return candidate
    raise RuntimeError("Could not create session directory — too many sessions on this date?")


def write_readme(session_dir: Path, fields: dict):
    template = README_TEMPLATE.read_text()
    for key, val in fields.items():
        template = template.replace("{{" + key + "}}", str(val))
    (session_dir / "README.md").write_text(template)


def write_session_summary(session_dir: Path):
    content = """# Session Summary

## What went well


## What went wrong


## Hints used
| Problem | Tier | At what point |
|---------|------|---------------|

## Time per problem
| Problem | Time spent | Solved? |
|---------|-----------|---------|

## Key takeaways for coding_patterns.md


## Problems to revisit

"""
    (session_dir / "session_summary.md").write_text(content)


def create_doubt_file(session_dir: Path, topic: str):
    slug = slugify(topic)
    content = f"""# Doubt: {topic}

## Confusion Point
What exactly confused you?

## Canonical Explanation
The correct explanation with concrete examples.

## Worked Example
Step-by-step walkthrough of a specific case.

## Analogies / Mental Models
How to think about this topic so it sticks.

## Common Mistakes
What people typically get wrong here.

## Test Question
A small problem to verify you understood:

> (write a small problem here)

## Answer to Test Question

"""
    path = session_dir / f"doubt_{slug}.md"
    path.write_text(content)
    print(f"  Created: {path}")


def create_problem_stub(session_dir: Path, slot: str):
    """Create a blank problem stub that the user can fill via fetch_problem.py."""
    path = session_dir / f"{slot}_tbd.cpp"
    path.write_text(f"// Problem for slot {slot}\n// Run: python3 scripts/fetch_problem.py --url <URL> --session {session_dir} --slot {slot}\n")
    test_path = session_dir / f"{slot}_tbd_tests.txt"
    test_path.write_text(f"# Test cases for {slot}\n# Run fetch_problem.py to populate\n")
    return path


def ask(prompt: str, default: str = "") -> str:
    val = input(f"{prompt} [{default}]: ").strip()
    return val if val else default


def main():
    parser = argparse.ArgumentParser(description="Create a new DSA session.")
    parser.add_argument("--type", choices=["contest", "practice", "doubt"], required=True)
    parser.add_argument("--company", help="Company name (for contest type)")
    parser.add_argument("--topic", help="Topic name (for practice/doubt type)")
    parser.add_argument("--duration", type=int, help="Duration in minutes")
    parser.add_argument("--num-problems", type=int, help="Number of problems (practice only, default 4)")
    parser.add_argument("--no-timer", action="store_true", help="Skip timer prompt")
    args = parser.parse_args()

    today = date.today().isoformat()

    # determine session name — use CLI args; only prompt if running interactively
    interactive = sys.stdin.isatty()

    if args.type == "contest":
        company = args.company or (ask("Company name", "Google") if interactive else "Google")
        session_name = f"{today}_{slugify(company)}"
        company_or_topic = company
        num_problems = 5
    elif args.type == "practice":
        topic = args.topic or (ask("Topic", "general") if interactive else "general")
        session_name = f"{today}_practice_{slugify(topic)}"
        company_or_topic = topic
        if args.num_problems:
            num_problems = args.num_problems
        elif interactive:
            num_problems = int(ask("Number of problems", "4"))
        else:
            num_problems = 4
    else:  # doubt
        topic = args.topic or (ask("Topic", "general") if interactive else "general")
        session_name = f"{today}_doubt_{slugify(topic)}"
        company_or_topic = topic
        num_problems = 0

    if args.duration:
        duration = args.duration
    elif interactive:
        duration = int(ask("Duration (minutes)", "90" if args.type == "contest" else "60"))
    else:
        duration = 90 if args.type == "contest" else 60

    print(f"\nCreating session: {session_name}")
    session_dir = make_session_dir(session_name)
    print(f"  Directory: {session_dir}")

    # create files
    if args.type == "doubt":
        create_doubt_file(session_dir, args.topic or "general")
        write_session_summary(session_dir)
        fields = {
            "SESSION_DIR": session_name,
            "DATE": today,
            "TYPE": "doubt",
            "COMPANY_OR_TOPIC": company_or_topic,
            "DURATION": duration,
            "LANG": "N/A",
            "P1_FILE": "—", "P1_TITLE": "—", "P1_DIFF": "—", "P1_TAGS": "—",
            "P2_FILE": "—", "P2_TITLE": "—", "P2_DIFF": "—", "P2_TAGS": "—",
            "P3_FILE": "—", "P3_TITLE": "—", "P3_DIFF": "—", "P3_TAGS": "—",
            "P4_FILE": "—", "P4_TITLE": "—", "P4_DIFF": "—", "P4_TAGS": "—",
            "P5_FILE": "—", "P5_TITLE": "—", "P5_DIFF": "—", "P5_TAGS": "—", "P5_ORIGIN": "—",
        }
        write_readme(session_dir, fields)
    else:
        # create problem stubs for all slots
        slots = [f"p{i}" for i in range(1, num_problems + 1)]
        if args.type == "contest":
            slots[-1] = "p5_REPEAT"  # last slot is always repeat in contest

        for slot in slots:
            create_problem_stub(session_dir, slot)

        write_session_summary(session_dir)

        # write README with TBD placeholders
        fields = {
            "SESSION_DIR": session_name,
            "DATE": today,
            "TYPE": args.type,
            "COMPANY_OR_TOPIC": company_or_topic,
            "DURATION": duration,
            "LANG": "C++",
        }
        for i, slot in enumerate(slots, 1):
            fields[f"P{i}_FILE"] = f"{slot}_tbd.cpp"
            fields[f"P{i}_TITLE"] = "TBD"
            fields[f"P{i}_DIFF"] = "?"
            fields[f"P{i}_TAGS"] = "?"
        # fill remaining slots if < 5
        for i in range(num_problems + 1, 6):
            fields[f"P{i}_FILE"] = "—"
            fields[f"P{i}_TITLE"] = "—"
            fields[f"P{i}_DIFF"] = "—"
            fields[f"P{i}_TAGS"] = "—"
        fields["P5_ORIGIN"] = "TBD (run select_repeat.py)"
        write_readme(session_dir, fields)

    print(f"\n{'='*55}")
    print(f"Session ready: {session_dir.relative_to(ROOT)}")
    print(f"{'='*55}")
    print("\nNext steps:")

    if args.type == "contest":
        print(f"  1. Get problem selections from Claude (share your coding_patterns.md)")
        print(f"  2. python3 scripts/select_repeat.py  → pick p5 repeat")
        print(f"  3. For each problem:")
        print(f"     python3 scripts/fetch_problem.py --url <URL> --session {session_dir} --slot p1")
        print(f"  4. Open problem files and start coding!")
        print(f"  5. python3 scripts/run_tests.py {session_dir}/<pN_file>.cpp")
    elif args.type == "practice":
        print(f"  1. Fetch problems: python3 scripts/fetch_problem.py --url <URL> --session {session_dir} --slot p1")
        print(f"  2. Code, test, repeat.")
    else:
        print(f"  1. Fill in the doubt_{slugify(company_or_topic)}.md file")
        print(f"  2. Work through the test question")
        print(f"  3. Add the key insight to coding_patterns.md")

    if not args.no_timer and args.type in ("contest", "practice") and interactive:
        start_timer = ask(f"\nStart {duration}-minute timer now?", "y").lower()
        if start_timer == "y":
            print(f"\nStarting timer... (Ctrl+C to stop)")
            try:
                subprocess.run([sys.executable, str(ROOT / "scripts" / "timer.py"), str(duration)])
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()
