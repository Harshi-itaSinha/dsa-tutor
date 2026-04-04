#!/usr/bin/env python3
"""
fetch_problem.py — Fetch a DSA problem from LeetCode, Codeforces, CSES, or stdin
and write it as a populated .cpp file using the problem template.

Usage:
  python3 scripts/fetch_problem.py --url <URL> --session <session_dir> --slot p1
  python3 scripts/fetch_problem.py --stdin --session sessions/2026-04-05_Google --slot p3
  python3 scripts/fetch_problem.py --url <URL>   # auto-detect session from cwd
"""

import argparse
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

# ── optional deps ─────────────────────────────────────────────────────────────
try:
    import requests
    from bs4 import BeautifulSoup
    import html2text
    DEPS_OK = True
except ImportError:
    DEPS_OK = False


ROOT = Path(__file__).parent.parent  # dsa-tutor/
TEMPLATE_FILE = ROOT / "templates" / "problem.cpp.template"
TEST_TEMPLATE_FILE = ROOT / "templates" / "testcases.template"


# ── helpers ───────────────────────────────────────────────────────────────────

def slugify(title: str) -> str:
    """'Two Sum' → 'two_sum'"""
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def read_template(path: Path) -> str:
    with open(path) as f:
        return f.read()


def fill_template(template: str, fields: dict) -> str:
    for key, val in fields.items():
        template = template.replace("{{" + key + "}}", str(val))
    return template


def h2t(html: str) -> str:
    """Convert HTML to plain text."""
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.body_width = 80
    return converter.handle(html).strip()


# ── platform fetchers ─────────────────────────────────────────────────────────

def fetch_leetcode(url: str) -> dict:
    """Fetch problem data from LeetCode GraphQL API."""
    # extract titleSlug from URL
    m = re.search(r"leetcode\.com/problems/([^/]+)", url)
    if not m:
        raise ValueError(f"Could not parse LeetCode URL: {url}")
    slug = m.group(1).rstrip("/")

    query = """
    query getQuestion($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        title
        difficulty
        content
        topicTags { name slug }
        exampleTestcases
        metaData
      }
    }
    """
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com",
        "User-Agent": "Mozilla/5.0",
    }
    resp = requests.post(
        "https://leetcode.com/graphql",
        json={"query": query, "variables": {"titleSlug": slug}},
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    q = data.get("data", {}).get("question")
    if not q:
        raise RuntimeError("LeetCode returned no data. Problem may be premium-only. Use --stdin.")

    tags = ", ".join(t["slug"] for t in (q.get("topicTags") or []))
    content_html = q.get("content") or ""
    content_text = h2t(content_html) if content_html else "(No content returned — may be premium)"

    # extract examples section
    examples_raw = q.get("exampleTestcases") or ""
    examples_formatted = "\n//   ".join(examples_raw.splitlines()) if examples_raw else "(see problem statement)"

    return {
        "title": q["title"],
        "slug": slugify(q["title"]),
        "difficulty": q.get("difficulty", "?"),
        "tags": tags,
        "platform": "LC",
        "url": url,
        "statement": content_text,
        "input_format": "(see problem statement)",
        "output_format": "(see problem statement)",
        "constraints": "(see problem statement)",
        "examples": examples_formatted,
    }


def fetch_codeforces(url: str) -> dict:
    """Scrape a Codeforces problem page."""
    # e.g. https://codeforces.com/contest/1234/problem/A
    #   or https://codeforces.com/problemset/problem/1234/A
    m = re.search(r"codeforces\.com/(?:contest|problemset/problem)/(\d+)/(?:problem/)?([A-Z]\d*)", url, re.I)
    if not m:
        raise ValueError(f"Could not parse Codeforces URL: {url}")
    contest_id, prob_index = m.group(1), m.group(2).upper()

    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    title_tag = soup.find("div", class_="title")
    title = title_tag.get_text(strip=True) if title_tag else f"CF {contest_id}{prob_index}"
    # remove leading "A. " prefix if present
    title = re.sub(r"^[A-Z]\d*\.\s*", "", title)

    statement_div = soup.find("div", class_="problem-statement")
    if not statement_div:
        raise RuntimeError("Could not find problem statement. Check the URL.")

    has_math = bool(statement_div.find("span", class_="MathJax"))
    statement_text = h2t(str(statement_div))

    input_spec = soup.find("div", class_="input-specification")
    input_text = h2t(str(input_spec)) if input_spec else "(see problem)"

    output_spec = soup.find("div", class_="output-specification")
    output_text = h2t(str(output_spec)) if output_spec else "(see problem)"

    # grab examples
    example_inputs = [tag.get_text() for tag in soup.select("div.input pre")]
    example_outputs = [tag.get_text() for tag in soup.select("div.output pre")]
    examples = ""
    for i, (inp, out) in enumerate(zip(example_inputs, example_outputs), 1):
        examples += f"Example {i}:\n//   Input:  {inp.strip()}\n//   Output: {out.strip()}\n//   "

    diff_tag = soup.find("span", class_="time-limit")
    difficulty = "CF"  # CF doesn't have Easy/Medium/Hard

    tags_elems = soup.select("span.tag-box")
    tags = ", ".join(t.get_text(strip=True) for t in tags_elems)

    extra = "\n// # MATH_CLEANUP_NEEDED — MathJax formulas may be garbled above" if has_math else ""

    return {
        "title": title,
        "slug": slugify(title),
        "difficulty": difficulty,
        "tags": tags or "cf",
        "platform": "CF",
        "url": url,
        "statement": statement_text + extra,
        "input_format": input_text,
        "output_format": output_text,
        "constraints": "(see problem — check time/memory limits on Codeforces)",
        "examples": examples.strip(),
    }


def fetch_cses(url: str) -> dict:
    """Scrape a CSES problem page."""
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "CSES Problem"

    content_div = soup.find("div", class_="content")
    if not content_div:
        content_div = soup.find("div", class_="task-body")

    statement_text = h2t(str(content_div)) if content_div else "(Could not parse CSES page)"

    return {
        "title": title,
        "slug": slugify(title),
        "difficulty": "CSES",
        "tags": "cses",
        "platform": "CSES",
        "url": url,
        "statement": statement_text,
        "input_format": "(see problem statement)",
        "output_format": "(see problem statement)",
        "constraints": "(see problem statement)",
        "examples": "(see problem statement)",
    }


def fetch_stdin() -> dict:
    """Interactively collect problem data from stdin."""
    print("=== Manual Problem Entry ===")
    print("(Press Enter twice to finish multi-line inputs)\n")

    title = input("Problem title: ").strip()
    url = input("Source URL (or 'custom'): ").strip() or "custom"
    platform = input("Platform (LC/CF/CSES/Custom): ").strip() or "Custom"
    difficulty = input("Difficulty (Easy/Medium/Hard): ").strip() or "?"
    tags = input("Tags (comma-separated, e.g. dp,backtracking): ").strip()

    print("\nPaste problem statement (blank line to finish):")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    statement = "\n".join(lines).strip()

    constraints = input("\nConstraints (one line summary): ").strip() or "(see statement)"
    examples = input("Examples (one line summary): ").strip() or "(see statement)"

    return {
        "title": title,
        "slug": slugify(title),
        "difficulty": difficulty,
        "tags": tags,
        "platform": platform,
        "url": url,
        "statement": statement,
        "input_format": "(see statement)",
        "output_format": "(see statement)",
        "constraints": constraints,
        "examples": examples,
    }


# ── main ──────────────────────────────────────────────────────────────────────

def detect_platform(url: str) -> str:
    if "leetcode.com" in url:
        return "leetcode"
    if "codeforces.com" in url:
        return "codeforces"
    if "cses.fi" in url:
        return "cses"
    return "unknown"


def fetch_problem_data(url: str | None, use_stdin: bool) -> dict:
    if use_stdin:
        return fetch_stdin()
    if not DEPS_OK:
        print("ERROR: Missing dependencies. Run: pip3 install requests beautifulsoup4 html2text")
        print("Or use --stdin to paste the problem manually.")
        sys.exit(1)
    platform = detect_platform(url)
    print(f"Fetching from {platform}: {url}")
    if platform == "leetcode":
        time.sleep(1)  # gentle rate limit
        return fetch_leetcode(url)
    elif platform == "codeforces":
        return fetch_codeforces(url)
    elif platform == "cses":
        return fetch_cses(url)
    else:
        print(f"Unknown platform for URL: {url}")
        print("Falling back to stdin mode.")
        return fetch_stdin()


def write_problem_file(problem: dict, out_path: Path, company: str, repeat_status: str):
    template = read_template(TEMPLATE_FILE)
    # wrap statement lines with // prefix
    stmt_lines = problem["statement"].splitlines()
    stmt_wrapped = "\n// ".join(stmt_lines)

    fields = {
        "TITLE": problem["title"],
        "URL": problem["url"],
        "PLATFORM": problem["platform"],
        "DATE": str(date.today()),
        "TAGS": problem["tags"],
        "DIFFICULTY": problem["difficulty"],
        "COMPANY": company,
        "REPEAT_STATUS": repeat_status,
        "STATEMENT": stmt_wrapped,
        "INPUT_FORMAT": problem["input_format"],
        "OUTPUT_FORMAT": problem["output_format"],
        "CONSTRAINTS": problem["constraints"],
        "EXAMPLES": problem["examples"],
        "HINT_1": "TODO — to be filled by Claude before the session starts",
        "HINT_2": "TODO — to be filled by Claude before the session starts",
        "TC": "?",
        "SC": "?",
    }
    content = fill_template(template, fields)
    out_path.write_text(content)
    print(f"  Written: {out_path}")


def write_test_file(problem: dict, out_path: Path):
    template = read_template(TEST_TEMPLATE_FILE)
    fields = {
        "TITLE": problem["title"],
        "PROBLEM_FILE": out_path.stem + ".cpp",
        "DATE": str(date.today()),
        "EXAMPLE_1_INPUT": "(fill in)",
        "EXAMPLE_1_OUTPUT": "(fill in)",
        "EDGE_MIN_INPUT": "(fill in)",
        "EDGE_MIN_OUTPUT": "(fill in)",
        "STRESS_INPUT": "(fill in)",
        "STRESS_OUTPUT": "(fill in)",
    }
    content = fill_template(template, fields)
    test_path = out_path.parent / (out_path.stem + "_tests.txt")
    test_path.write_text(content)
    print(f"  Written: {test_path}")


def main():
    parser = argparse.ArgumentParser(description="Fetch a DSA problem and create problem + test files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="URL of the problem (LeetCode, Codeforces, CSES)")
    group.add_argument("--stdin", action="store_true", help="Enter problem interactively via stdin")
    parser.add_argument("--session", help="Session directory path (e.g. sessions/2026-04-05_Google)", default=".")
    parser.add_argument("--slot", help="Problem slot (p1–p5, or p5_REPEAT)", default="p1")
    parser.add_argument("--company", help="Company name for the session", default="practice")
    parser.add_argument("--repeat", help="Repeat status string (e.g. 'YES — from 2026-03-10_Google')", default="NO")
    args = parser.parse_args()

    session_dir = Path(args.session)
    if not session_dir.exists():
        print(f"Session directory does not exist: {session_dir}")
        print("Run new_session.py first, or create the directory manually.")
        sys.exit(1)

    problem = fetch_problem_data(args.url, args.stdin)

    slot = args.slot
    slug = problem["slug"]
    if "REPEAT" in slot.upper():
        filename = f"{slot.lower()}_{slug}.cpp"
    else:
        filename = f"{slot}_{slug}.cpp"

    out_path = session_dir / filename
    if out_path.exists():
        overwrite = input(f"{out_path} already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != "y":
            print("Aborted.")
            sys.exit(0)

    write_problem_file(problem, out_path, args.company, args.repeat)
    write_test_file(problem, out_path)

    print(f"\nDone. Edit {out_path} to add hints and test cases.")


if __name__ == "__main__":
    main()
