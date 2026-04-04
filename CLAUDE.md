# DSA Tutor — Claude Context

This is a file-based DSA tutoring system for Harshita. Read this before every session.

## User Profile
- Language: **C++** (primary)
- Weak areas: **DP, Backtracking, Advanced DS (Tries/Seg Tree/Heaps/DSU), Mixed multi-DS problems**
- Platforms: LeetCode, Codeforces, CSES, manual paste
- Goal: Simulate company OA contests, track patterns, improve weaknesses systematically

## Project Layout
```
coding_patterns.md    ← READ THIS FIRST — current weaknesses, mistakes, progress
question_bank.md      ← all problems with status/tags/history (28 seeded)
session_log.md        ← one-row log per session
sessions/             ← YYYY-MM-DD_<type>/ subdirs, each with p1–p5 .cpp + _tests.txt
scripts/              ← all automation
templates/            ← .cpp and test file skeletons
```

## Session Types & Commands
```bash
# Contest (5 problems: 4 new + 1 repeat)
python3 scripts/new_session.py --type contest --company Google

# Practice (topic drill)
python3 scripts/new_session.py --type practice --topic dp

# Doubt session
python3 scripts/new_session.py --type doubt --topic "segment tree"

# Countdown timer
python3 scripts/timer.py 90
```

## How to Fetch Problems

### By URL
```bash
python3 scripts/fetch_problem.py --url <URL> --session sessions/<dir> --slot p1
```
Supported:
- **LeetCode**: full statement via GraphQL API (`/graphql` endpoint, `titleSlug` query)
- **Codeforces**: metadata (name, rating, tags) via official API `https://codeforces.com/api/problemset.problems`; HTML scraping for statement (may hit 403 — user pastes manually)
- **CSES**: HTML scrape of `.content` div

### Manual paste
```bash
python3 scripts/fetch_problem.py --stdin --session sessions/<dir> --slot p1
```

### Discover CF problems by tag + rating (for question bank seeding)
```bash
python3 scripts/fetch_problem.py --discover-cf --cf-tags dp --cf-min 1400 --cf-max 2000 --count 10
# Returns list of matching problems with URLs — copy into question_bank.md
```

### CF API Details
- Endpoint: `https://codeforces.com/api/problemset.problems`
- Optional param: `tags` (semicolon-separated, e.g. `?tags=dp;greedy`)
- Returns: `{ status: "OK", result: { problems: [{contestId, index, name, type, rating?, points?, tags[]}] } }`
- Problem URL format: `https://codeforces.com/problemset/problem/{contestId}/{index}`
- **CF HTML scraping blocked by Cloudflare** → file is created with API metadata; statement placeholder tells user to paste manually

## Running Tests
```bash
python3 scripts/run_tests.py sessions/<dir>/p1_<slug>.cpp   # single problem
python3 scripts/run_tests.py sessions/<dir>/                # whole session
```
Test file format (`p1_<slug>_tests.txt`):
```
---TEST 1--- label
INPUT
<stdin lines>
EXPECTED
<stdout>
# UNORDERED   ← sort lines before compare
# FLOAT       ← epsilon 1e-6 compare
```

## Contest Problem Selection (for Claude)
When starting a contest, read `coding_patterns.md` → WEAKNESSES section, then:
- p1: Easy warm-up (not from a weakness topic)
- p2: Medium targeting weakness #1
- p3: Medium targeting weakness #2 or mixed-DS
- p4: Hard targeting a weak area
- p5: Run `python3 scripts/select_repeat.py` → pick from top-3 candidates

## Hint Rules
- **NEVER** show Tier 2 hint unless user explicitly asks or has been stuck 30+ min
- Tier 1 = gentle nudge, no algorithm spoilers
- Tier 2 = concrete approach + time/space complexity

## Post-Session
```bash
python3 scripts/update_patterns.py --session sessions/<dir>
git add . && git commit -m "Session: YYYY-MM-DD <type>"
git push
```

## Repeat Question Rules
- p5 (repeat) must NOT come from the immediately preceding session
- Eligibility: status = solved/attempted, not used in last 2 sessions
- Weighting: needs-review > attempted > solved; weakness tags ×2; >10 sessions ago ×1.5
- Run `select_repeat.py --dry-run` to preview top candidates

## Key Files Claude Should Read Each Session
1. `coding_patterns.md` — current state, weaknesses, recent progress
2. `question_bank.md` — problem statuses and what's been used
3. `session_log.md` — to identify the immediately preceding session (for repeat exclusion)
