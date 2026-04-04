#!/usr/bin/env python3
"""
select_repeat.py — Select the repeat problem (p5) for a contest session.

Usage:
  python3 scripts/select_repeat.py
  python3 scripts/select_repeat.py --dry-run   # show top-5 candidates with scores
  python3 scripts/select_repeat.py --exclude Q003,Q007

Reads:
  question_bank.md   — problem status, tags, session history
  session_log.md     — to identify the immediately preceding session
  coding_patterns.md — to read current weaknesses
"""

import argparse
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
BANK_FILE  = ROOT / "question_bank.md"
LOG_FILE   = ROOT / "session_log.md"
PATTERNS_FILE = ROOT / "coding_patterns.md"


# ── parse question bank ────────────────────────────────────────────────────────

def parse_question_bank() -> list[dict]:
    """Parse the Quick Index table from question_bank.md."""
    text = BANK_FILE.read_text()
    # find the table rows after the header
    table_section = re.search(r"\| ID.*?\n\|[-| ]+\n((?:\|.*\n)+)", text)
    if not table_section:
        print("ERROR: Could not parse Quick Index table in question_bank.md")
        sys.exit(1)

    problems = []
    for line in table_section.group(1).splitlines():
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) < 9:
            continue
        qid, title, platform, tags, diff, status, last_used, times_used, repeat_eligible = cols[:9]
        problems.append({
            "id": qid,
            "title": title,
            "tags": [t.strip() for t in tags.split(",")],
            "difficulty": diff,
            "status": status,
            "last_used": last_used if last_used != "—" else None,
            "times_used": int(times_used) if times_used.isdigit() else 0,
            "repeat_eligible": repeat_eligible,
        })
    return problems


def parse_session_log() -> list[str]:
    """Return list of session directory names from session_log.md, oldest first."""
    text = LOG_FILE.read_text()
    sessions = []
    for line in text.splitlines():
        if line.startswith("|") and not line.startswith("| Date") and "---" not in line:
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if cols and re.match(r"\d{4}-\d{2}-\d{2}", cols[0]):
                sessions.append(cols[0])  # date field
    return sessions


def parse_weaknesses() -> list[str]:
    """Extract the top weakness topics from coding_patterns.md."""
    text = PATTERNS_FILE.read_text()
    # look for "## WEAKNESSES" section
    m = re.search(r"## WEAKNESSES.*?\n(.*?)(?=\n##|\Z)", text, re.DOTALL)
    if not m:
        return []
    section = m.group(1)
    # extract lowercase keywords from numbered list items
    keywords = []
    for line in section.splitlines():
        line = line.strip()
        if re.match(r"\d+\.", line):
            # grab first significant word(s)
            words = re.sub(r"\*\*([^*]+)\*\*.*", r"\1", line)
            words = re.sub(r"\d+\.\s*", "", words).lower()
            keywords.append(words.strip())
    return keywords


def parse_session_problems(session_dir_name: str) -> set[str]:
    """Return problem IDs used in a session by scanning session README."""
    session_dir = ROOT / "sessions" / session_dir_name
    readme = session_dir / "README.md"
    if not readme.exists():
        return set()
    text = readme.read_text()
    # look for Q### mentions
    return set(re.findall(r"Q\d{3}", text))


# ── scoring ───────────────────────────────────────────────────────────────────

def score_problem(p: dict, sessions: list[str], weaknesses: list[str], recent_sessions: set[str]) -> float:
    status = p["status"]
    if status not in ("solved", "attempted", "needs-review"):
        return 0.0  # unseen or never-used

    if p["repeat_eligible"].startswith("never"):
        return 0.0

    # check if used in a recent session (last 2)
    last_used = p["last_used"]
    if last_used:
        session_dates = sessions[-2:] if len(sessions) >= 2 else sessions
        if any(last_used in s for s in session_dates):
            return 0.0

    # base weight
    base = {"needs-review": 3.0, "attempted": 2.0, "solved": 1.0}.get(status, 1.0)

    # recency boost: sessions since last used
    sessions_since = len(sessions)
    if last_used:
        for i, s in enumerate(sessions):
            if last_used in s:
                sessions_since = len(sessions) - i
                break
    if sessions_since > 10:
        recency = 1.5
    elif sessions_since >= 4:
        recency = 1.0
    else:
        recency = 0.8

    # weakness boost
    tags_lower = " ".join(p["tags"]).lower()
    weakness_match = any(w.split()[0] in tags_lower for w in weaknesses[:4])
    strength_keywords = ["arrays", "greedy", "binary-search"]  # rough placeholder
    strength_match = any(k in tags_lower for k in strength_keywords)

    if weakness_match:
        wb = 2.0
    elif strength_match:
        wb = 0.7
    else:
        wb = 1.0

    return base * recency * wb


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Select the repeat problem (p5) for a contest.")
    parser.add_argument("--dry-run", action="store_true", help="Show top candidates without selecting")
    parser.add_argument("--exclude", help="Comma-separated problem IDs to exclude (e.g. Q003,Q007)")
    args = parser.parse_args()

    excluded = set(args.exclude.split(",")) if args.exclude else set()

    problems = parse_question_bank()
    sessions = parse_session_log()
    weaknesses = parse_weaknesses()

    # get problems used in the immediately preceding session
    if sessions:
        prev_session_problems = parse_session_problems(sessions[-1])
    else:
        prev_session_problems = set()

    # score
    candidates = []
    for p in problems:
        if p["id"] in excluded:
            continue
        if p["id"] in prev_session_problems:
            continue
        s = score_problem(p, sessions, weaknesses, prev_session_problems)
        if s > 0:
            candidates.append((s, p))

    if not candidates:
        print("No eligible repeat candidates found.")
        print("Make sure you have solved or attempted at least one problem in a prior session.")
        sys.exit(0)

    candidates.sort(key=lambda x: -x[0])
    top = candidates[:5]

    print("\n=== Repeat Problem Candidates (p5) ===\n")
    for rank, (score, p) in enumerate(top, 1):
        marker = " ← recommended" if rank == 1 else ""
        print(f"  {rank}. [{p['id']}] {p['title']}")
        print(f"     Score: {score:.2f}  |  Status: {p['status']}  |  Tags: {', '.join(p['tags'])}")
        print(f"     Last used: {p['last_used'] or 'never'}{marker}\n")

    if args.dry_run:
        print("(dry-run mode — no selection made)")
        return

    # random pick among top-3 to avoid determinism
    pick_pool = top[:min(3, len(top))]
    _, chosen = random.choice(pick_pool)

    print(f"\nSelected: [{chosen['id']}] {chosen['title']}")
    print(f"  Tags:       {', '.join(chosen['tags'])}")
    print(f"  Status:     {chosen['status']}")
    print(f"  Last used:  {chosen['last_used'] or 'never'}")
    print(f"\nFetch it with:")
    print(f"  python3 scripts/fetch_problem.py --url <URL> --slot p5_REPEAT --repeat 'YES — from {chosen['last_used']}'")


if __name__ == "__main__":
    main()
