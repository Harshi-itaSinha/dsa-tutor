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
from typing import Optional

# ── optional deps ─────────────────────────────────────────────────────────────
try:
    import requests
    from bs4 import BeautifulSoup
    import html2text
    DEPS_OK = True
except ImportError:
    DEPS_OK = False

try:
    import cloudscraper
    CF_SCRAPER = cloudscraper.create_scraper()
except ImportError:
    CF_SCRAPER = None


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


CF_API_BASE = "https://codeforces.com/api"

# Codeforces API: problemset.problems
#   GET https://codeforces.com/api/problemset.problems
#   Optional params: tags (semicolon-separated), problemsetName
#   Returns: { status: "OK", result: { problems: [...], problemStatistics: [...] } }
#   Each problem: { contestId, index, name, type, points?, rating?, tags[] }
#
#   NOTE: The API has no endpoint to fetch a single problem by ID —
#   the full (or tag-filtered) list is returned and we filter locally.
#   Tag-filtered requests (e.g. ?tags=dp) are much smaller (~hundreds vs thousands).


def cf_api_fetch_problems(tags: Optional[list] = None) -> list:
    """
    Call https://codeforces.com/api/problemset.problems and return the problems list.
    If `tags` is given, pass them as a semicolon-separated filter to reduce payload.
    """
    params = {}
    if tags:
        params["tags"] = ";".join(tags)
    resp = requests.get(f"{CF_API_BASE}/problemset.problems", params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "OK":
        raise RuntimeError(f"Codeforces API error: {data.get('comment', 'unknown')}")
    return data["result"]["problems"]


def cf_api_get_problem_meta(contest_id: str, prob_index: str) -> Optional[dict]:
    """
    Fetch metadata for a single CF problem by contestId + index.

    Strategy: the API doesn't support fetching one problem directly.
    We call problemset.problems unfiltered (finds any problem) and search locally.
    Falls back gracefully if the API is unreachable or the problem isn't in the set
    (e.g. educational rounds, gym contests).
    """
    try:
        problems = cf_api_fetch_problems()  # no tag filter — we don't know tags yet
        for p in problems:
            if str(p.get("contestId")) == contest_id and p.get("index", "").upper() == prob_index.upper():
                return p
    except Exception as e:
        print(f"  [warn] CF API lookup failed: {e}")
    return None


def cf_discover_problems(
    tags: list[str],
    min_rating: int = 0,
    max_rating: int = 9999,
    count: int = 10,
) -> list[dict]:
    """
    Discover CF problems matching given tags and difficulty range.
    Uses https://codeforces.com/api/problemset.problems?tags=<tag1;tag2>

    Returns up to `count` problems sorted by rating ascending.
    Useful for seeding the question bank with targeted problems.
    """
    problems = cf_api_fetch_problems(tags=tags)
    filtered = [
        p for p in problems
        if min_rating <= p.get("rating", 0) <= max_rating
        and p.get("rating")  # exclude problems with no rating
    ]
    filtered.sort(key=lambda p: p.get("rating", 0))
    return filtered[:count]


def fetch_codeforces(url: str) -> dict:
    """
    Fetch a Codeforces problem.
    - Metadata (name, rating, tags): Codeforces official REST API
      https://codeforces.com/api/problemset.problems
    - Problem statement text: HTML scrape (API does not expose statement text)
    """
    # parse contest_id and problem index from URL
    # Valid CF URL formats:
    #   https://codeforces.com/contest/1234/problem/A
    #   https://codeforces.com/problemset/problem/1234/A
    #   https://codeforces.com/gym/1234/problem/A
    m = re.search(
        r"codeforces\.com/(?:contest|problemset/problem|gym)/(\d+)/(?:problem/)?([A-Z]\d*)",
        url, re.I
    )
    if not m:
        raise ValueError(
            f"Could not parse Codeforces URL: {url}\n"
            "Valid formats:\n"
            "  https://codeforces.com/contest/1234/problem/A\n"
            "  https://codeforces.com/problemset/problem/1234/A"
        )
    contest_id, prob_index = m.group(1), m.group(2).upper()

    # ── Step 1: fetch metadata via official API ────────────────────────────────
    print(f"  Querying Codeforces API for contest {contest_id}, problem {prob_index}...")
    meta = cf_api_get_problem_meta(contest_id, prob_index)

    if meta:
        title = meta.get("name", f"CF{contest_id}{prob_index}")
        rating = meta.get("rating")
        api_tags = ", ".join(meta.get("tags", []))
        # map numeric rating to a rough difficulty label
        if rating:
            if rating <= 1200:   difficulty = f"CF-Easy ({rating})"
            elif rating <= 1800: difficulty = f"CF-Medium ({rating})"
            else:                difficulty = f"CF-Hard ({rating})"
        else:
            difficulty = "CF"
        print(f"  API: name='{title}', rating={rating}, tags=[{api_tags}]")
    else:
        print("  API lookup failed or problem not in problemset — falling back to HTML for metadata.")
        title = None
        api_tags = None
        difficulty = "CF"

    # ── Step 2: scrape HTML for the problem statement (API doesn't return it) ─
    # cloudscraper handles Cloudflare JS challenge; plain requests gets 403
    time.sleep(1)  # brief pause before HTML fetch
    statement_text = input_text = output_text = examples = None
    extra = ""

    try:
        # cloudscraper bypasses Cloudflare JS challenge that blocks plain requests
        if CF_SCRAPER:
            resp = CF_SCRAPER.get(url, timeout=20)
        else:
            print("  [warn] cloudscraper not installed — falling back to requests (may get 403)")
            print("  Install with: pip3 install cloudscraper")
            resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # fallback title from HTML if API failed
        if not title:
            title_tag = soup.find("div", class_="title")
            title = title_tag.get_text(strip=True) if title_tag else f"CF {contest_id}{prob_index}"
            title = re.sub(r"^[A-Z]\d*\.\s*", "", title)

        statement_div = soup.find("div", class_="problem-statement")
        if statement_div:
            has_math = bool(statement_div.find("span", class_="MathJax"))

            # extract input/output/note text BEFORE decomposing them
            input_spec  = statement_div.find("div", class_="input-specification")
            output_spec = statement_div.find("div", class_="output-specification")
            input_text  = h2t(str(input_spec)).strip()  if input_spec  else "(see problem)"
            output_text = h2t(str(output_spec)).strip() if output_spec else "(see problem)"

            # now strip noise from the statement: header (title/limits), input, output, samples, note
            for tag in statement_div.find_all("div", class_=["header",
                                                               "input-specification",
                                                               "output-specification",
                                                               "sample-tests",
                                                               "note"]):
                tag.decompose()

            statement_text = h2t(str(statement_div)).strip()
            extra = "\n// # MATH_CLEANUP_NEEDED — MathJax formulas may be garbled above" if has_math else ""

        # examples from HTML
        example_inputs  = [tag.get_text() for tag in soup.select("div.input pre")]
        example_outputs = [tag.get_text() for tag in soup.select("div.output pre")]
        examples = ""
        for i, (inp, out) in enumerate(zip(example_inputs, example_outputs), 1):
            examples += f"Example {i}:\n//   Input:  {inp.strip()}\n//   Output: {out.strip()}\n//   "
        examples = examples.strip()

        # fallback tags from HTML if API didn't return them
        if not api_tags:
            tags_elems = soup.select("span.tag-box")
            api_tags = ", ".join(t.get_text(strip=True) for t in tags_elems) or "cf"

    except Exception as e:
        # HTML scraping blocked (CF uses Cloudflare) — use API metadata only
        print(f"  [warn] HTML scrape failed ({e})")
        print(f"  Statement unavailable via scraping. Open the problem at:\n    {url}")
        print("  Paste the statement into the file manually after it's created.\n")
        if not title:
            title = f"CF{contest_id}{prob_index}"
        statement_text = (
            f"PASTE STATEMENT HERE\n"
            f"// Open: {url}\n"
            f"// Copy the problem statement and replace this placeholder."
        )
        input_text = "(paste from problem page)"
        output_text = "(paste from problem page)"
        examples = "(paste from problem page)"

    return {
        "title": title,
        "slug": slugify(title),
        "difficulty": difficulty,
        "tags": api_tags or "cf",
        "platform": "CF",
        "url": url,
        "statement": (statement_text or "") + extra,
        "input_format": input_text or "(see problem)",
        "output_format": output_text or "(see problem)",
        "constraints": "(see problem — check time/memory limits on Codeforces)",
        "examples": examples or "(see problem)",
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


def fetch_problem_data(url: Optional[str], use_stdin: bool) -> dict:
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


def _wrap(text: str) -> str:
    """Prefix every line with '// ' so it sits cleanly inside C++ comments."""
    return "\n// ".join(text.splitlines())


def _strip_heading(text: str, *headings) -> str:
    """Remove redundant first-line headings like 'Input', 'Output'."""
    lines = text.splitlines()
    if lines and lines[0].strip() in headings:
        lines = lines[1:]
    return "\n".join(lines).strip()


def write_problem_file(problem: dict, out_path: Path, company: str, repeat_status: str):
    template = read_template(TEMPLATE_FILE)

    input_text = _strip_heading(problem["input_format"], "Input", "INPUT")
    output_text = _strip_heading(problem["output_format"], "Output", "OUTPUT")

    fields = {
        "TITLE": problem["title"],
        "URL": problem["url"],
        "PLATFORM": problem["platform"],
        "DATE": str(date.today()),
        "TAGS": problem["tags"],
        "DIFFICULTY": problem["difficulty"],
        "COMPANY": company,
        "REPEAT_STATUS": repeat_status,
        "STATEMENT": _wrap(problem["statement"]),
        "INPUT_FORMAT": _wrap(input_text),
        "OUTPUT_FORMAT": _wrap(output_text),
        "CONSTRAINTS": _wrap(problem["constraints"]),
        "EXAMPLES": _wrap(problem["examples"]),
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


def cmd_discover_cf(args):
    """
    --discover-cf mode: query CF API for problems by tag and rating range,
    print a formatted list you can copy into question_bank.md.

    Example:
      python3 scripts/fetch_problem.py --discover-cf --cf-tags dp --cf-min 1400 --cf-max 2000 --count 10
    """
    if not DEPS_OK:
        print("ERROR: pip3 install requests beautifulsoup4 html2text")
        sys.exit(1)

    tags = [t.strip() for t in args.cf_tags.split(",")]
    print(f"\nQuerying CF API: tags={tags}, rating={args.cf_min}–{args.cf_max}, count={args.count}")
    print("API: https://codeforces.com/api/problemset.problems?tags=" + ";".join(tags))
    print()

    try:
        problems = cf_discover_problems(tags, args.cf_min, args.cf_max, args.count)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not problems:
        print("No problems found matching those filters.")
        return

    print(f"Found {len(problems)} problem(s):\n")
    print(f"{'#':<3} {'ID':<12} {'Rating':<8} {'Name':<45} {'Tags'}")
    print("-" * 100)
    for i, p in enumerate(problems, 1):
        pid = f"{p['contestId']}{p['index']}"
        url = f"https://codeforces.com/problemset/problem/{p['contestId']}/{p['index']}"
        tag_str = ", ".join(p.get("tags", []))
        print(f"{i:<3} {pid:<12} {p.get('rating', '?'):<8} {p['name'][:44]:<45} {tag_str}")
        print(f"    URL: {url}")
    print()
    print("Copy the URLs above and use:")
    print("  python3 scripts/fetch_problem.py --url <URL> --session <dir> --slot p1")


def main():
    parser = argparse.ArgumentParser(description="Fetch a DSA problem and create problem + test files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="URL of the problem (LeetCode, Codeforces, CSES)")
    group.add_argument("--stdin", action="store_true", help="Enter problem interactively via stdin")
    group.add_argument(
        "--discover-cf",
        action="store_true",
        help="Discover CF problems by tag/rating using the CF API (no file created)"
    )
    parser.add_argument("--session", help="Session directory path (e.g. sessions/2026-04-05_Google)", default=".")
    parser.add_argument("--slot", help="Problem slot (p1–p5, or p5_REPEAT)", default="p1")
    parser.add_argument("--company", help="Company name for the session", default="practice")
    parser.add_argument("--repeat", help="Repeat status string (e.g. 'YES — from 2026-03-10_Google')", default="NO")
    # --discover-cf options
    parser.add_argument("--cf-tags", help="Comma-separated CF tags to search (e.g. 'dp,greedy')", default="dp")
    parser.add_argument("--cf-min", type=int, help="Minimum CF rating", default=800)
    parser.add_argument("--cf-max", type=int, help="Maximum CF rating", default=2400)
    parser.add_argument("--count", type=int, help="Max problems to return in --discover-cf", default=10)
    args = parser.parse_args()

    if args.discover_cf:
        cmd_discover_cf(args)
        return

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
