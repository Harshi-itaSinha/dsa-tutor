#!/usr/bin/env python3
"""
update_patterns.py — Update coding_patterns.md after a session.

Usage:
  python3 scripts/update_patterns.py --session sessions/2026-04-05_Google
  python3 scripts/update_patterns.py --weekly-report
"""

import argparse
import re
import shutil
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
PATTERNS_FILE = ROOT / "coding_patterns.md"
ARCHIVE_DIR = ROOT / "archive" / "patterns_history"
LOG_FILE = ROOT / "session_log.md"


def backup_patterns():
    """Snapshot coding_patterns.md before modifying it."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    snap = ARCHIVE_DIR / f"coding_patterns_{date.today().isoformat()}.md"
    shutil.copy(PATTERNS_FILE, snap)
    print(f"  Snapshot saved: {snap.relative_to(ROOT)}")


def parse_session_summary(session_dir: Path) -> dict:
    """Parse session_summary.md into a structured dict."""
    summary_file = session_dir / "session_summary.md"
    if not summary_file.exists():
        return {}
    text = summary_file.read_text()

    def extract_section(header):
        m = re.search(rf"## {re.escape(header)}\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
        return m.group(1).strip() if m else ""

    return {
        "went_well": extract_section("What went well"),
        "went_wrong": extract_section("What went wrong"),
        "hints": extract_section("Hints used"),
        "time_per_problem": extract_section("Time per problem"),
        "takeaways": extract_section("Key takeaways for coding_patterns.md"),
        "revisit": extract_section("Problems to revisit"),
    }


def count_solved(session_dir: Path) -> tuple[int, int]:
    """Count solved/total from test results in README."""
    readme = session_dir / "README.md"
    if not readme.exists():
        return 0, 0
    text = readme.read_text()
    passes = re.findall(r"✓ All pass", text)
    total_rows = re.findall(r"p\d.*\.cpp", text)
    return len(passes), len(total_rows)


def update_dashboard(patterns_text: str, topics_used: list[str]) -> str:
    """Increment the Attempted count for topics seen in this session."""
    # This is a simple heuristic: just note which topics were practiced
    # The user should manually update Solved/Comfort after reviewing
    note = f"\n_Topics practiced in last session: {', '.join(set(topics_used)) if topics_used else 'unknown'}_\n"
    # insert after the dashboard table
    patterns_text = re.sub(
        r"(_Comfort scale.*?_\n)",
        r"\1" + note,
        patterns_text,
        count=1,
    )
    return patterns_text


def append_progress_note(patterns_text: str, session_name: str, summary: dict, solved: int, total: int) -> str:
    """Append a new entry to the PROGRESS NOTES section."""
    session_date = date.today().isoformat()

    hints_short = summary.get("hints", "").strip() or "—"
    # truncate long hints text
    if len(hints_short) > 200:
        hints_short = hints_short[:200] + "..."

    takeaways = summary.get("takeaways", "").strip() or "—"

    note = f"""
### {session_date} — {session_name}
- Solved: {solved}/{total} problems
- Went well: {summary.get('went_well', '—').strip()[:200]}
- Went wrong: {summary.get('went_wrong', '—').strip()[:200]}
- Hints used: {hints_short[:200]}
- Takeaways: {takeaways[:300]}
"""
    patterns_text = patterns_text.replace(
        "## PROGRESS NOTES\n_Newest first — add after each session_\n",
        "## PROGRESS NOTES\n_Newest first — add after each session_\n" + note,
    )
    return patterns_text


def update_last_updated(patterns_text: str) -> str:
    today = date.today().isoformat()
    # update the header line
    patterns_text = re.sub(
        r"_Last updated: [\d-]+",
        f"_Last updated: {today}",
        patterns_text,
    )
    # increment sessions count
    def inc_sessions(m):
        n = int(m.group(1)) + 1
        return f"Sessions completed: {n}"
    patterns_text = re.sub(r"Sessions completed: (\d+)", inc_sessions, patterns_text)
    return patterns_text


def extract_topics_from_session(session_dir: Path) -> list[str]:
    """Get tags/topics from problem files in the session."""
    topics = []
    for cpp_file in session_dir.glob("p*.cpp"):
        text = cpp_file.read_text()
        m = re.search(r"// TAGS:\s*(.+)", text)
        if m:
            tags = [t.strip() for t in m.group(1).split(",")]
            topics.extend(tags)
    return topics


def append_to_session_log(session_dir: Path, solved: int, total: int, duration: int):
    """Add a row to session_log.md."""
    text = LOG_FILE.read_text()
    today = date.today().isoformat()
    session_type = "practice"
    if "_doubt_" in session_dir.name:
        session_type = "doubt"
    elif re.search(r"_[A-Z][a-z]", session_dir.name):
        session_type = "contest"

    company_topic = session_dir.name.replace(f"{today}_", "")
    row = f"| {today} | {session_type} | {company_topic} | {total} | {solved} | — | {duration} min | |"
    text += "\n" + row
    LOG_FILE.write_text(text)
    print(f"  Session log updated.")


def generate_weekly_report():
    """Print a one-page weekly progress summary."""
    text = PATTERNS_FILE.read_text()
    log_text = LOG_FILE.read_text()

    today = date.today()
    week_ago = (today - timedelta(days=7)).isoformat()
    today_str = today.isoformat()

    print(f"\n{'='*60}")
    print(f"  WEEKLY DSA PROGRESS REPORT")
    print(f"  {week_ago} → {today_str}")
    print(f"{'='*60}\n")

    # count sessions this week
    sessions_this_week = []
    for line in log_text.splitlines():
        if line.startswith("|") and re.match(r"\| \d{4}-\d{2}-\d{2}", line):
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if cols[0] >= week_ago:
                sessions_this_week.append(cols)

    print(f"Sessions this week: {len(sessions_this_week)}")
    total_solved = sum(int(s[4]) for s in sessions_this_week if s[4].isdigit())
    total_attempted = sum(int(s[3]) for s in sessions_this_week if s[3].isdigit())
    print(f"Problems: {total_solved}/{total_attempted} solved\n")

    # extract weaknesses
    m = re.search(r"## WEAKNESSES.*?\n(.*?)(?=\n##)", text, re.DOTALL)
    if m:
        print("Current weaknesses (priority order):")
        for line in m.group(1).strip().splitlines():
            if line.strip():
                print(f"  {line.strip()}")
        print()

    # recent progress notes
    m2 = re.search(r"## PROGRESS NOTES\n.*?\n(.*?)(?=\Z)", text, re.DOTALL)
    if m2:
        notes = m2.group(1)
        # show last 2 session entries
        entries = re.split(r"### \d{4}-\d{2}-\d{2}", notes)[:3]
        if entries:
            print("Recent session notes:")
            for e in entries[1:3]:
                print(e.strip()[:400])
                print()

    print(f"{'='*60}")
    print("Recommendation: run `python3 scripts/new_session.py` to continue.\n")


def main():
    parser = argparse.ArgumentParser(description="Update coding_patterns.md after a session.")
    parser.add_argument("--session", help="Session directory path (e.g. sessions/2026-04-05_Google)")
    parser.add_argument("--weekly-report", action="store_true", help="Print weekly progress summary")
    parser.add_argument("--duration", type=int, default=90, help="Session duration in minutes")
    args = parser.parse_args()

    if args.weekly_report:
        generate_weekly_report()
        return

    if not args.session:
        print("Provide --session <path> or --weekly-report")
        sys.exit(1)

    session_dir = Path(args.session)
    if not session_dir.exists():
        # try relative to ROOT
        session_dir = ROOT / args.session
    if not session_dir.exists():
        print(f"Session directory not found: {args.session}")
        sys.exit(1)

    session_name = session_dir.name
    print(f"\nUpdating patterns for session: {session_name}")

    # backup first
    backup_patterns()

    summary = parse_session_summary(session_dir)
    solved, total = count_solved(session_dir)
    topics = extract_topics_from_session(session_dir)

    patterns_text = PATTERNS_FILE.read_text()
    patterns_text = update_last_updated(patterns_text)
    patterns_text = update_dashboard(patterns_text, topics)
    patterns_text = append_progress_note(patterns_text, session_name, summary, solved, total)
    PATTERNS_FILE.write_text(patterns_text)

    append_to_session_log(session_dir, solved, total, args.duration)

    print(f"\n  coding_patterns.md updated.")
    print(f"  Solved: {solved}/{total} problems")
    if topics:
        print(f"  Topics covered: {', '.join(set(topics))}")

    print("\n  Manual tasks remaining:")
    print("  - Update Comfort scores in the SUMMARY DASHBOARD table")
    print("  - Add any new recurring mistakes to the RECURRING MISTAKES table")
    print("  - Update question_bank.md status for solved problems")
    print("  - git add . && git commit -m 'Session: ...' && git push")


if __name__ == "__main__":
    main()
