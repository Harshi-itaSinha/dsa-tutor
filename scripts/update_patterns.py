#!/usr/bin/env python3
"""
update_patterns.py — Auto-update coding_patterns.md after a session.

Extracts from each p*.cpp file:
  - Tags (from // TAGS: line)
  - Confidence (1-5) from YOUR NOTES section
  - Time spent from YOUR NOTES or session_summary.md
  - Hints used (Tier 1 / Tier 2)
  - Edge cases missed

Extracts from session README.md:
  - Tests passed / total per problem

Updates coding_patterns.md:
  - SUMMARY DASHBOARD: Attempted, Solved, Avg Time, Comfort, Priority
  - Header: Problems solved count, last updated date, sessions count
  - TOPIC HISTORY: appends problem slug per topic
  - RECURRING MISTAKES: prompts interactively if new mistakes found
  - PROGRESS NOTES: appends session summary

Usage:
  python3 scripts/update_patterns.py --session sessions/2026-04-05_Google
  python3 scripts/update_patterns.py --weekly-report
"""

import argparse
import re
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
PATTERNS_FILE = ROOT / "coding_patterns.md"
ARCHIVE_DIR   = ROOT / "archive" / "patterns_history"
LOG_FILE      = ROOT / "session_log.md"

# ── Tag → Dashboard row mapping ───────────────────────────────────────────────
# Maps lowercase tag fragments to the exact row name in the SUMMARY DASHBOARD

TAG_TO_ROW = {
    "two pointer":             "Arrays / Two Pointers",
    "two pointers":            "Arrays / Two Pointers",
    "array":                   "Arrays / Two Pointers",
    "sliding window":          "Sliding Window",
    "binary search":           "Binary Search",
    "linked list":             "Linked Lists",
    "stack":                   "Stacks & Queues",
    "queue":                   "Stacks & Queues",
    "monotonic stack":         "Stacks & Queues",
    "monotonic queue":         "Stacks & Queues",
    "tree":                    "Trees / BFS / DFS",
    "bfs":                     "Trees / BFS / DFS",
    "dfs":                     "Graphs",
    "dfs and similar":         "Graphs",
    "graphs":                  "Graphs",
    "graph":                   "Graphs",
    "shortest path":           "Graphs",
    "dynamic programming":     "Dynamic Programming",
    "dp":                      "Dynamic Programming",
    "backtracking":            "Backtracking",
    "heap":                    "Heaps / Priority Queue",
    "priority queue":          "Heaps / Priority Queue",
    "trie":                    "Tries",
    "union find":              "Union-Find (DSU)",
    "dsu":                     "Union-Find (DSU)",
    "disjoint set":            "Union-Find (DSU)",
    "segment tree":            "Segment Tree / BIT",
    "binary indexed tree":     "Segment Tree / BIT",
    "fenwick":                 "Segment Tree / BIT",
    "mixed":                   "Mixed Multi-DS",
    "greedy":                  "Greedy",
    "bit manipulation":        "Bit Manipulation",
    "string":                  "Strings",
    "strings":                 "Strings",
    "constructive":            "Greedy",   # CF tag, closest match
}

PRIORITY_THRESHOLDS = {
    "HIGH": lambda c: c < 2.5,
    "—":    lambda c: 2.5 <= c <= 3.5,
    "LOW":  lambda c: c > 3.5,
}


# ── Per-problem data extraction ───────────────────────────────────────────────

def extract_problem_data(cpp_file: Path) -> dict:
    """Parse a .cpp problem file and extract all trackable data."""
    text = cpp_file.read_text()

    # tags — line format: "// ADDED: ...  |  TAGS: ..."  OR  "// TAGS: ..."
    tags_m = re.search(r"\bTAGS:\s*(.+)", text)
    tags = [t.strip().lower() for t in tags_m.group(1).split(",")] if tags_m else []

    # slug from filename
    slug = cpp_file.stem  # e.g. p1_max_tree

    # confidence
    conf_m = re.search(r"Confidence\s*\(1-5\)\s*:\s*([1-5])", text)
    confidence = int(conf_m.group(1)) if conf_m else None

    # time spent
    time_m = re.search(r"Time\s*(?:spent|complexity)?\s*:\s*([^\n]+)", text, re.I)
    # distinguish "Time complexity:" from "Time spent:" - we want time spent
    time_spent_m = re.search(r"(?:time spent|time taken)\s*:\s*([^\n]+)", text, re.I)
    time_spent = time_spent_m.group(1).strip() if time_spent_m else None

    # hints used — check if TODO is still in place (= not filled by Claude = hints given)
    tier1_given = "TODO" not in text and bool(re.search(
        r"\[TIER 1 HINT.*?\].*?\n//\s*(.+)", text))
    tier2_given = "TODO" not in text and bool(re.search(
        r"\[TIER 2 HINT.*?\].*?\n//\s*(.+)", text))
    # simpler heuristic: check if hints section was filled (not TODO)
    hints_section = re.search(
        r"\[TIER 1 HINT[^\]]*\].*?-+\n(.*?)\[TIER 2", text, re.DOTALL)
    tier1_filled = hints_section and "TODO" not in hints_section.group(1)
    hints_section2 = re.search(
        r"\[TIER 2 HINT[^\]]*\].*?-+\n(.*?)Time complexity", text, re.DOTALL)
    tier2_filled = hints_section2 and "TODO" not in hints_section2.group(1)

    hints_used = []
    if tier1_filled: hints_used.append("Tier 1")
    if tier2_filled: hints_used.append("Tier 2")

    # edge cases missed
    edge_m = re.search(r"Edge cases missed\s*:\s*([^\n]+)", text)
    edge_cases = edge_m.group(1).strip() if edge_m else None

    # approach tried
    approach_m = re.search(r"Approach tried\s*:\s*([^\n]+)", text)
    approach = approach_m.group(1).strip() if approach_m else None

    return {
        "file":        cpp_file.name,
        "slug":        slug,
        "tags":        tags,
        "confidence":  confidence,
        "time_spent":  time_spent,
        "hints_used":  hints_used,
        "edge_cases":  edge_cases if edge_cases and edge_cases != "?" else None,
        "approach":    approach if approach and approach != "?" else None,
    }


def extract_test_results(session_dir: Path) -> dict:
    """
    Parse test results from session README.md.
    Returns dict: {filename: {"passed": int, "total": int}}
    run_tests.py appends rows like:
      | p1_two_sum.cpp | 4 | 5 | ✓ All pass |
    """
    readme = session_dir / "README.md"
    results = {}
    if not readme.exists():
        return results
    for line in readme.read_text().splitlines():
        # match test result rows
        m = re.match(r"\|\s*(p\d+\S+\.cpp)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", line)
        if m:
            fname, passed, total = m.group(1), int(m.group(2)), int(m.group(3))
            results[fname] = {"passed": passed, "total": total}
    return results


# ── Dashboard update ──────────────────────────────────────────────────────────

def tags_to_rows(tags: list) -> list:
    """Map problem tags to matching SUMMARY DASHBOARD row names."""
    rows = set()
    for tag in tags:
        tag_lower = tag.lower()
        for key, row in TAG_TO_ROW.items():
            if key in tag_lower or tag_lower in key:
                rows.add(row)
                break
    return list(rows)


def parse_dashboard(patterns_text: str) -> list:
    """
    Parse the SUMMARY DASHBOARD table into a list of row dicts.
    Returns list of dicts with keys: pattern, comfort, attempted, solved, avg_time, priority
    """
    rows = []
    in_table = False
    for line in patterns_text.splitlines():
        if "## SUMMARY DASHBOARD" in line:
            in_table = True
            continue
        if in_table:
            if line.startswith("##"):
                break
            m = re.match(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
            if m and not line.startswith("| Pattern") and "---" not in line:
                rows.append({
                    "pattern":   m.group(1).strip(),
                    "comfort":   m.group(2).strip(),
                    "attempted": int(m.group(3)),
                    "solved":    int(m.group(4)),
                    "avg_time":  m.group(5).strip(),
                    "priority":  m.group(6).strip(),
                })
    return rows


def compute_new_comfort(old_comfort_str: str, new_confidence: int) -> str:
    """
    Rolling average of confidence scores → comfort level.
    Weight: existing score counts as 3 observations, new as 1 (so it moves gradually).
    """
    try:
        old = float(old_comfort_str)
        # weighted average: old score weighted 3x so comfort moves gradually
        new_val = (old * 3 + new_confidence) / 4
        return f"{new_val:.1f}"
    except ValueError:
        # was '?' — first real data point
        return str(float(new_confidence))


def compute_avg_time(old_avg: str, new_time_str: str) -> str:
    """Update rolling average time. Expects strings like '25 min'."""
    def parse_mins(s):
        m = re.search(r"(\d+)", s or "")
        return int(m.group(1)) if m else None

    new_mins = parse_mins(new_time_str)
    if not new_mins:
        return old_avg  # can't update without a time

    old_mins = parse_mins(old_avg)
    if not old_mins:
        return f"{new_mins} min"

    avg = (old_mins + new_mins) // 2
    return f"{avg} min"


def compute_priority(comfort_str: str) -> str:
    try:
        c = float(comfort_str)
        if c < 2.5:   return "HIGH"
        elif c <= 3.5: return "—"
        else:           return "LOW"
    except ValueError:
        return "—"


def rebuild_dashboard_table(rows: list) -> str:
    """Rebuild the markdown table from row dicts."""
    header = "| Pattern | Comfort (1–5) | Attempted | Solved | Avg Time | Priority |"
    sep    = "|---------|---------------|-----------|--------|----------|----------|"
    lines  = [header, sep]
    for r in rows:
        lines.append(
            f"| {r['pattern']} | {r['comfort']} | {r['attempted']} | {r['solved']} | {r['avg_time']} | {r['priority']} |"
        )
    return "\n".join(lines)


def update_dashboard(patterns_text: str, problems: list, test_results: dict) -> tuple:
    """
    Update SUMMARY DASHBOARD rows based on this session's problems.
    Returns (updated_text, total_solved_this_session).
    """
    rows = parse_dashboard(patterns_text)
    row_index = {r["pattern"]: i for i, r in enumerate(rows)}

    session_solved = 0

    for prob in problems:
        conf       = prob["confidence"]
        time_spent = prob["time_spent"]
        tr         = test_results.get(prob["file"], {})
        tests_ok   = tr.get("passed", 0) == tr.get("total", 1) and tr.get("total", 0) > 0

        # "solved" = all tests pass OR confidence >= 3 (when tests weren't run)
        solved_this = tests_ok or (conf is not None and conf >= 3)
        if solved_this:
            session_solved += 1

        target_rows = tags_to_rows(prob["tags"])
        for row_name in target_rows:
            if row_name not in row_index:
                continue
            i = row_index[row_name]
            rows[i]["attempted"] += 1
            if solved_this:
                rows[i]["solved"] += 1
            if conf is not None:
                rows[i]["comfort"] = compute_new_comfort(rows[i]["comfort"], conf)
                rows[i]["priority"] = compute_priority(rows[i]["comfort"])
            if time_spent:
                rows[i]["avg_time"] = compute_avg_time(rows[i]["avg_time"], time_spent)

    # rebuild the table in the text
    old_table_m = re.search(
        r"(\| Pattern \| Comfort.*?\n(?:\|.*\n)*)",
        patterns_text
    )
    if old_table_m:
        new_table = rebuild_dashboard_table(rows) + "\n"
        patterns_text = patterns_text.replace(old_table_m.group(1), new_table)

    return patterns_text, session_solved


# ── Header update ─────────────────────────────────────────────────────────────

def update_header(patterns_text: str, new_solved: int) -> str:
    today = date.today().isoformat()
    # last updated date
    patterns_text = re.sub(r"_Last updated: [\d-]+", f"_Last updated: {today}", patterns_text)
    # sessions count
    patterns_text = re.sub(
        r"Sessions completed: (\d+)",
        lambda m: f"Sessions completed: {int(m.group(1)) + 1}",
        patterns_text
    )
    # problems solved count
    patterns_text = re.sub(
        r"Problems solved: (\d+)",
        lambda m: f"Problems solved: {int(m.group(1)) + new_solved}",
        patterns_text
    )
    return patterns_text


# ── Topic history update ──────────────────────────────────────────────────────

def update_topic_history(patterns_text: str, problems: list, session_name: str) -> str:
    """Append problem slugs to the TOPIC HISTORY section."""
    for prob in problems:
        target_rows = tags_to_rows(prob["tags"])
        # map row names back to topic keys used in TOPIC HISTORY
        row_to_key = {v: k.replace(" ", "-").replace("/", "").lower()
                      for k, v in TAG_TO_ROW.items()}
        for row_name in target_rows:
            key = row_to_key.get(row_name, row_name.lower().replace(" ", "-"))
            entry = f"{prob['slug']}@{session_name}"
            # find the line and append if not already there
            def append_entry(m):
                line = m.group(0)
                if entry in line:
                    return line
                return line.rstrip() + f", {entry}"
            patterns_text = re.sub(
                rf"^{re.escape(key)}:.*$",
                append_entry,
                patterns_text,
                flags=re.MULTILINE
            )
    return patterns_text


# ── Progress note ─────────────────────────────────────────────────────────────

def append_progress_note(patterns_text: str, session_name: str, problems: list,
                         test_results: dict, summary: dict, session_solved: int) -> str:
    today = date.today().isoformat()
    total = len(problems)

    # build per-problem lines
    prob_lines = []
    for p in problems:
        tr = test_results.get(p["file"], {})
        tests_str = f"{tr.get('passed','?')}/{tr.get('total','?')} tests" if tr else "tests not run"
        conf_str  = f"confidence {p['confidence']}/5" if p["confidence"] else "confidence not rated"
        hints_str = f"hints: {', '.join(p['hints_used'])}" if p["hints_used"] else "no hints"
        edge_str  = f" | missed: {p['edge_cases']}" if p["edge_cases"] else ""
        prob_lines.append(f"  - {p['file']}: {tests_str}, {conf_str}, {hints_str}{edge_str}")

    took = summary.get("went_well", "").strip()[:150] or "—"
    wrong = summary.get("went_wrong", "").strip()[:150] or "—"
    takeaways = summary.get("takeaways", "").strip()[:300] or "—"

    prob_block = "\n".join(prob_lines)
    note = f"""
### {today} — {session_name}
- Result: {session_solved}/{total} solved
- Problems:
{prob_block}
- Went well: {took}
- Went wrong: {wrong}
- Takeaways: {takeaways}
"""
    patterns_text = patterns_text.replace(
        "## PROGRESS NOTES\n_Newest first — add after each session_\n",
        "## PROGRESS NOTES\n_Newest first — add after each session_\n" + note,
    )
    return patterns_text


# ── Session log ───────────────────────────────────────────────────────────────

def append_to_session_log(session_dir: Path, problems: list,
                          session_solved: int, duration: int):
    today = date.today().isoformat()
    name = session_dir.name

    session_type = "doubt" if "_doubt_" in name else \
                   "contest" if not "_practice_" in name else "practice"
    company_topic = re.sub(rf"^{today}_", "", name)

    total = len(problems)
    hints_used = sum(1 for p in problems if p["hints_used"])
    hints_str = f"{hints_used} problem(s)" if hints_used else "none"

    row = f"| {today} | {session_type} | {company_topic} | {total} | {session_solved} | {hints_str} | {duration} min | |"
    text = LOG_FILE.read_text()
    text += "\n" + row
    LOG_FILE.write_text(text)
    print(f"  session_log.md updated")


# ── Recurring mistakes prompt ─────────────────────────────────────────────────

def prompt_mistakes(problems: list):
    """If edge cases were missed, suggest adding them to RECURRING MISTAKES."""
    missed = [(p["file"], p["edge_cases"]) for p in problems if p["edge_cases"]]
    if not missed:
        return
    print("\n  ── New edge cases to consider logging ──")
    for fname, ec in missed:
        print(f"  {fname}: {ec}")
    print("  → Add these to RECURRING MISTAKES in coding_patterns.md manually or in next session.")


# ── Print session report ──────────────────────────────────────────────────────

def print_report(problems: list, test_results: dict, session_solved: int):
    total = len(problems)
    print(f"\n{'='*55}")
    print(f"  SESSION REPORT")
    print(f"{'='*55}")
    print(f"  Solved: {session_solved}/{total}\n")

    for p in problems:
        tr   = test_results.get(p["file"], {})
        conf = p["confidence"]
        conf_bar = ("★" * conf + "☆" * (5 - conf)) if conf else "not rated"
        tests_str = f"{tr.get('passed','?')}/{tr.get('total','?')} tests pass" if tr else "no test data"
        hints_str = ", ".join(p["hints_used"]) if p["hints_used"] else "none"
        print(f"  {p['file']}")
        print(f"    Confidence : {conf_bar}")
        print(f"    Tests      : {tests_str}")
        print(f"    Hints used : {hints_str}")
        if p["edge_cases"]:
            print(f"    Edge cases : {p['edge_cases']}")
        print()

    print(f"  Topics practiced: {', '.join(set(t for p in problems for t in tags_to_rows(p['tags'])))}")
    print(f"{'='*55}")


# ── Weekly report ─────────────────────────────────────────────────────────────

def generate_weekly_report():
    text     = PATTERNS_FILE.read_text()
    log_text = LOG_FILE.read_text()
    today    = date.today()
    week_ago = (today - timedelta(days=7)).isoformat()

    print(f"\n{'='*60}")
    print(f"  WEEKLY DSA PROGRESS REPORT  {week_ago} → {today.isoformat()}")
    print(f"{'='*60}\n")

    sessions_this_week = []
    for line in log_text.splitlines():
        if line.startswith("|") and re.match(r"\|\s*\d{4}-\d{2}-\d{2}", line):
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cols) >= 5 and cols[0] >= week_ago:
                sessions_this_week.append(cols)

    total_solved    = sum(int(s[4]) for s in sessions_this_week if len(s)>4 and s[4].isdigit())
    total_attempted = sum(int(s[3]) for s in sessions_this_week if len(s)>3 and s[3].isdigit())
    print(f"  Sessions   : {len(sessions_this_week)}")
    print(f"  Problems   : {total_solved}/{total_attempted} solved\n")

    # dashboard summary — show rows with HIGH priority
    rows = parse_dashboard(text)
    high = [r for r in rows if r["priority"] == "HIGH"]
    if high:
        print("  Current HIGH priority topics (needs work):")
        for r in high:
            print(f"    {r['pattern']:<30} comfort={r['comfort']}  {r['attempted']} attempted / {r['solved']} solved")
        print()

    improving = [r for r in rows if r["comfort"] not in ("?", "—") and float(r["comfort"]) >= 3.5]
    if improving:
        print("  Topics trending well (comfort >= 3.5):")
        for r in improving:
            print(f"    {r['pattern']:<30} comfort={r['comfort']}")
        print()

    # recent progress notes
    m = re.search(r"## PROGRESS NOTES\n.*?\n(.*?)(?=\Z)", text, re.DOTALL)
    if m:
        entries = re.split(r"(?=### \d{4}-\d{2}-\d{2})", m.group(1).strip())
        if entries:
            print("  Recent session notes:")
            for e in entries[:2]:
                if e.strip():
                    print("  " + e.strip()[:300].replace("\n", "\n  "))
                    print()

    print(f"{'='*60}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session",  help="Session directory (e.g. sessions/2026-04-05_Google)")
    parser.add_argument("--weekly-report", action="store_true")
    parser.add_argument("--duration", type=int, default=90, help="Session duration in minutes")
    args = parser.parse_args()

    if args.weekly_report:
        generate_weekly_report()
        return

    if not args.session:
        print("Usage: python3 scripts/update_patterns.py --session <dir>")
        sys.exit(1)

    session_dir = Path(args.session)
    if not session_dir.exists():
        session_dir = ROOT / args.session
    if not session_dir.exists():
        print(f"Session not found: {args.session}")
        sys.exit(1)

    session_name = session_dir.name
    print(f"\nUpdating patterns for: {session_name}")

    # ── 1. extract data from all problem files ─────────────────────────────
    cpp_files = sorted(f for f in session_dir.glob("p*.cpp")
                       if "tbd" not in f.name)
    problems = [extract_problem_data(f) for f in cpp_files]

    if not problems:
        print("  No problem files found (p*.cpp). Nothing to update.")
        sys.exit(0)

    # ── 2. extract test results from README ────────────────────────────────
    test_results = extract_test_results(session_dir)

    # ── 3. parse session_summary.md ────────────────────────────────────────
    summary_file = session_dir / "session_summary.md"
    summary = {}
    if summary_file.exists():
        text = summary_file.read_text()
        def section(h):
            m = re.search(rf"## {re.escape(h)}\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
            return m.group(1).strip() if m else ""
        summary = {
            "went_well":  section("What went well"),
            "went_wrong": section("What went wrong"),
            "takeaways":  section("Key takeaways for coding_patterns.md"),
        }

    # ── 4. backup coding_patterns.md ──────────────────────────────────────
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    snap = ARCHIVE_DIR / f"coding_patterns_{date.today().isoformat()}.md"
    shutil.copy(PATTERNS_FILE, snap)
    print(f"  Snapshot: {snap.relative_to(ROOT)}")

    # ── 5. update coding_patterns.md ──────────────────────────────────────
    patterns_text = PATTERNS_FILE.read_text()
    patterns_text, session_solved = update_dashboard(patterns_text, problems, test_results)
    patterns_text = update_header(patterns_text, session_solved)
    patterns_text = update_topic_history(patterns_text, problems, session_name)
    patterns_text = append_progress_note(patterns_text, session_name, problems,
                                         test_results, summary, session_solved)
    PATTERNS_FILE.write_text(patterns_text)
    print(f"  coding_patterns.md updated")

    # ── 6. update session_log.md ──────────────────────────────────────────
    append_to_session_log(session_dir, problems, session_solved, args.duration)

    # ── 7. print session report ────────────────────────────────────────────
    print_report(problems, test_results, session_solved)

    # ── 8. flag missed edge cases ──────────────────────────────────────────
    prompt_mistakes(problems)

    print("\n  Remaining manual steps:")
    print("  - Add new recurring mistakes to RECURRING MISTAKES table if any")
    print("  - Update question_bank.md status for solved problems")
    print("  - git add . && git commit -m 'Session: ...' && git push")


if __name__ == "__main__":
    main()
