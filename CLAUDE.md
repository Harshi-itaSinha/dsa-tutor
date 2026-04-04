# DSA Tutor — Claude Context

This is a file-based DSA tutoring system for Harshita. Read this before every session.

---

## HOW TO RESUME — read this if the user says "load dsa-tutor context from claude.md"

1. **Read these files in order** (use the Read tool):
   - `CLAUDE.md` (this file — you are here)
   - `coding_patterns.md` — current weaknesses, comfort scores, recent progress notes
   - `session_log.md` — last few rows to identify the most recent session
   - `question_bank.md` — skim the Quick Index table for problem statuses

2. **Check what needs testing next** — see the "What Needs to Be Tested Next" section below and tell the user the current status in one paragraph.

3. **Ask the user what they want to do**:
   - Start a new contest/practice/doubt session
   - Test/fix a script
   - Add problems to the bank
   - Get a progress report

4. **Do NOT re-explain the whole project** — just summarize current status and ask.

**Project location:** `/Users/harshita/Desktop/Coding/dsa-tutor/`
**GitHub:** https://github.com/Harshi-itaSinha/dsa-tutor
**Always `git pull` first** if resuming on a different machine.

---

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

---

## Build Status (as of 2026-04-05)

### What Was Built and How

**Phase 1 — Scaffold** ✅ DONE
- `README.md`, `SETUP.md`, `WORKFLOW.md`, `problem_selection.md` — full documentation
- `coding_patterns.md` — pre-filled with Harshita's known weak areas (DP, Backtracking, Advanced DS, Mixed multi-DS), patterns reference with C++ code snippets for DP/Trie/DSU/Monotonic Stack
- `question_bank.md` — 28 problems seeded across weak topics (DP×10, Backtracking×6, Advanced DS×8, Mixed×4), each with notes, repeat weight, and LeetCode URLs
- `session_log.md` — header only, ready to be filled
- `templates/problem.cpp.template` — C++ file with problem statement, Tier 1/2 hints, YOUR NOTES all as comment blocks
- `templates/testcases.template` — test file format with INPUT/EXPECTED blocks and flag comments
- `templates/session_readme.template` — per-session README skeleton
- `git init` + initial commit

**Phase 2 — Core Scripts** ✅ DONE
- `scripts/fetch_problem.py`
  - LeetCode: GraphQL API (`/graphql`, `titleSlug` query) → full statement + examples ✅ UNTESTED end-to-end
  - Codeforces: official REST API (`/api/problemset.problems`) for metadata (name, rating, tags) ✅ TESTED AND WORKING; HTML scrape for statement → **blocked by Cloudflare 403**, graceful fallback creates file with placeholder, user pastes statement manually ✅ TESTED
  - `--discover-cf`: tag+rating filtered CF API query, prints matching problems ✅ TESTED AND WORKING
  - CSES: HTML scrape of `.content` div ✅ UNTESTED
  - `--stdin`: interactive paste mode ✅ UNTESTED
  - Fixed Python 3.9 `X | None` type hint incompatibility ✅ FIXED
- `scripts/run_tests.py` — compile C++17, parse `_tests.txt`, run with 2s TLE, compare output (supports UNORDERED, FLOAT flags), append results to session README ✅ WRITTEN, UNTESTED end-to-end
- `scripts/timer.py` — countdown with per-minute alerts at 30/15/10/5/2/1 min, terminal bell ✅ WRITTEN, UNTESTED

**Phase 3 — Session Management Scripts** ✅ DONE
- `scripts/new_session.py` — creates session dir, problem stubs, README, session_summary.md, optionally launches timer ✅ WRITTEN, UNTESTED
- `scripts/select_repeat.py` — reads question_bank + session_log + coding_patterns, scores candidates, outputs top-3 ✅ WRITTEN; tested with empty bank → correct "no candidates" output ✅
- `scripts/update_patterns.py` — backs up coding_patterns.md to archive/, appends progress note, updates last-updated/session count, appends to session_log ✅ WRITTEN, UNTESTED
- `CLAUDE.md` (this file) ✅ DONE

**GitHub** ⏳ PENDING
- Local git repo initialized with 3 commits ✅
- Remote not yet connected — user needs to create private repo `dsa-tutor` on github.com and run:
  ```bash
  git remote add origin https://github.com/<username>/dsa-tutor.git
  git push -u origin main
  ```

---

### What Needs to Be Tested Next (in order)

**1. LeetCode fetch** — UNTESTED
```bash
mkdir -p sessions/test_lc
python3 scripts/fetch_problem.py --url https://leetcode.com/problems/two-sum/ --session sessions/test_lc --slot p1 --company test
```
Expected: `p1_two_sum.cpp` with full problem statement in comment header, tags, difficulty.
Watch for: rate limiting (add delay if needed), premium problem check.

**2. CSES fetch** — UNTESTED
```bash
mkdir -p sessions/test_cses
python3 scripts/fetch_problem.py --url https://cses.fi/problemset/task/1068 --session sessions/test_cses --slot p1 --company test
```
Expected: `p1_weird_algorithm.cpp` with statement text. CSES may also block scraping — same fallback applies.

**3. run_tests.py** — UNTESTED end-to-end
- Write a trivial C++ solution (e.g. echo input), add test cases to `_tests.txt`, run:
```bash
python3 scripts/run_tests.py sessions/test_lc/p1_two_sum.cpp
```
Expected: PASS/FAIL per test, summary line, result appended to session README.
Watch for: g++ path on macOS (`/usr/bin/g++`), stdin piping edge cases, TLE detection.

**4. new_session.py** — UNTESTED
```bash
python3 scripts/new_session.py --type practice --topic dp --no-timer
```
Expected: `sessions/YYYY-MM-DD_practice_dp/` with p1–p4 stubs, README, session_summary.md.

**5. update_patterns.py** — UNTESTED
After running a session and filling session_summary.md:
```bash
python3 scripts/update_patterns.py --session sessions/<dir>
```
Expected: archive snapshot created, progress note appended to coding_patterns.md, session_log.md row added.

**6. Full contest end-to-end** — UNTESTED
```bash
python3 scripts/new_session.py --type contest --company Amazon --no-timer
# fetch 5 problems, write solutions, run tests, update patterns
```

---

### Known Issues / Limitations

| Issue | Severity | Status |
|-------|----------|--------|
| CF HTML scraping blocked by Cloudflare (403) | Medium | Handled — graceful fallback with placeholder |
| LeetCode GraphQL untested | Medium | Test next session |
| CSES scraping untested | Low | Test next session |
| `run_tests.py` untested with real C++ | High | Test next session |
| `new_session.py` untested | High | Test next session |
| GitHub remote not set up | Low | User needs to create repo and push |
| Python 3.9 on macOS (system python) — all scripts use `Optional` not `X \| None` | Fixed | ✅ |
| g++ compiler path may vary — test `g++ --version` first | Low | Check during run_tests test |
| urllib3 SSL warning (LibreSSL on macOS) — cosmetic only | Cosmetic | Suppress with `PYTHONWARNINGS=ignore` prefix if annoying |
