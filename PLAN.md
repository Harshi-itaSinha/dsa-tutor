# DSA Tutor — Project Plan

This file documents the full plan discussed and built for this project.

---

## Goal

Build a fully self-contained, file-based DSA tutoring system that:
- Simulates company OA contests (Google, Amazon, etc.) with 5 timed problems
- Tracks weaknesses and growth through a central `coding_patterns.md`
- Auto-generates and runs test cases against C++ solutions
- Uses weakness data to intelligently select and repeat problems
- Needs no external SaaS tools — everything lives in files and git

**Primary language:** C++
**Platforms:** LeetCode, Codeforces, CSES, manual paste
**Weak areas to address:** DP, Backtracking, Advanced DS (Tries / Seg Tree / Heaps / DSU), Mixed multi-DS problems

---

## Project Structure

```
dsa-tutor/
├── README.md                    — quick-start and overview
├── SETUP.md                     — installation and one-time setup
├── WORKFLOW.md                  — step-by-step for every session type
├── PLAN.md                      — this file
├── CLAUDE.md                    — Claude context: how to resume sessions
├── problem_selection.md         — algorithm for choosing and repeating problems
├── coding_patterns.md           — central tracker: patterns, mistakes, strengths/weaknesses
├── question_bank.md             — all problems with status, tags, history (28 seeded)
├── session_log.md               — one-row log per session
│
├── templates/
│   ├── problem.cpp.template     — C++ file with comment blocks pre-filled
│   ├── testcases.template       — test file format with INPUT/EXPECTED blocks
│   └── session_readme.template  — per-session README skeleton
│
├── scripts/
│   ├── new_session.py           — bootstrap a session directory + all stubs
│   ├── fetch_problem.py         — fetch from LC/CF/CSES URL or --stdin paste
│   ├── run_tests.py             — compile + run C++ against _tests.txt, report failures
│   ├── select_repeat.py         — weighted selection of the p5 repeat problem
│   ├── timer.py                 — countdown timer in terminal
│   └── update_patterns.py       — auto-update coding_patterns.md after a session
│
├── include/
│   └── bits/stdc++.h            — macOS compatibility shim (Apple Clang doesn't ship it)
│
├── archive/
│   └── patterns_history/        — snapshot of coding_patterns.md before each update
│
└── sessions/
    └── YYYY-MM-DD_<type>/
        ├── README.md            — session metadata + test results (auto-appended)
        ├── p1_<slug>.cpp        — problem statement + hints + solution
        ├── p1_<slug>_tests.txt  — test cases in INPUT/EXPECTED format
        ├── p5_REPEAT_<slug>.cpp — repeat problem (always p5 in contests)
        └── session_summary.md   — filled post-session by user
```

---

## Session Types

| Type | Purpose | Problems | Duration |
|------|---------|----------|----------|
| `contest` | Full company OA simulation | 5 (4 new + 1 repeat) | 90 min |
| `practice` | Topic-focused drill | 3–5 | 60 min |
| `doubt` | Clarify a concept | 1 + explanation doc | open |

---

## Problem File Format

Each `p1_<slug>.cpp` has this structure in its comment header:

```
// PROBLEM: <Title>
// SOURCE:  <URL>  |  Platform: LC / CF / CSES / Custom
// ADDED:   <YYYY-MM-DD>  |  TAGS: <dp, backtracking, ...>
// DIFFICULTY: <Easy/Medium/Hard>  |  COMPANY: <Google / ...>
// REPEAT: NO

// PROBLEM STATEMENT: ...full text...
// Input: ...
// Output: ...
// Constraints: ...

// [TIER 1 HINT — Nudge]:
//   gentle direction, no spoilers

// [TIER 2 HINT — Concrete approach, read after 30+ min stuck]:
//   specific algorithm + time/space complexity

// YOUR NOTES (fill after solving):
//   Approach tried:
//   Time complexity:
//   Space complexity:
//   Edge cases missed:
//   Confidence (1-5):
```

---

## Test Case File Format

```
---TEST 1--- basic case
INPUT
2 7 11 15
9
EXPECTED
0 1

---TEST 2--- edge: negatives
INPUT
-3 -2 -1
-5
EXPECTED
0 2
# UNORDERED   <- sort output lines before comparing (for any-order problems)
# FLOAT       <- use epsilon 1e-6 for floating-point comparison
# DRIVER      <- class-based problem, needs manual wrapper (runner skips)
# INTERACTIVE <- interactive problem (runner skips)
```

---

## Problem Fetching Strategy

| Source | Method |
|--------|--------|
| LeetCode URL | GraphQL API (`/graphql`, `titleSlug` query) — full statement |
| Codeforces URL | Official REST API (`/api/problemset.problems`) for metadata; `cloudscraper` for HTML statement (bypasses Cloudflare) |
| CSES URL | HTML scrape of `.content` div via BeautifulSoup |
| Manual paste | `--stdin` flag — prompts for raw text |
| CF discovery | `--discover-cf --cf-tags dp --cf-min 1400 --cf-max 2000` — finds problems by tag+rating |

**Dependencies:** `pip install requests beautifulsoup4 html2text cloudscraper`

---

## Contest Problem Selection (how Claude picks problems)

When starting a contest, Claude reads `coding_patterns.md` → WEAKNESSES section, then selects:

| Slot | Role | Selection rule |
|------|------|----------------|
| p1 | Easy warm-up | Not from a weakness topic; Easy difficulty |
| p2 | Medium | Targets weakness #1 |
| p3 | Medium | Targets weakness #2 or mixed-DS |
| p4 | Hard | Targets a weak area |
| p5 | Repeat | Run `select_repeat.py` — weighted from question bank |

---

## Repeat Question Selection Rules

`select_repeat.py` scores all eligible problems and returns the top 3 candidates.

**Hard exclude:** problems from the immediately preceding session.

**Eligibility:** status = `solved` or `attempted`; last used ≥ 2 sessions ago.

**Scoring weights:**
- `needs-review` → ×3 weight
- `attempted` → ×2 weight
- `solved` → ×1 weight
- Tags match a current weakness → ×2
- Tags match a strength → ×0.7
- Last used > 10 sessions ago → ×1.5 (reinforce old learning)

---

## `coding_patterns.md` Structure

```
# Coding Patterns Tracker
_Last updated: <date> | Sessions completed: N | Problems solved: N_

## SUMMARY DASHBOARD
| Pattern | Comfort (1–5) | Attempted | Solved | Avg Time | Priority |

## RECURRING MISTAKES
| Date | Problem | Mistake | Category | Fix/Lesson |

## STRENGTHS
## WEAKNESSES (priority order)
## PATTERNS REFERENCE (C++ code snippets for key patterns)
## TOPIC HISTORY (problem IDs per topic, for repeat selection weighting)
## PROGRESS NOTES (newest first — appended after each session)
```

`update_patterns.py` auto-updates the dashboard after every session by:
- Parsing `Confidence (1-5):` from each `p*.cpp` file
- Parsing test results from session `README.md`
- Rolling comfort average: `(old × 3 + new_confidence) / 4`
- Recomputing priority: `< 2.5 → HIGH`, `2.5–3.5 → —`, `> 3.5 → LOW`
- Appending a progress note with per-problem breakdown

---

## Test Runner Flow (`run_tests.py`)

1. Compile: `g++ -O2 -std=c++17 -Wall -I include/ <file>.cpp -o /tmp/dsa_runner_<name>`
2. Parse `_tests.txt` by `---TEST N---` markers
3. Run each test: pipe input into binary, capture stdout, 2-second TLE limit
4. Compare output (strip whitespace; `# UNORDERED` → sort lines; `# FLOAT` → epsilon 1e-6)
5. Report: `✓ TEST 1` / `✗ TEST 2 — Expected: X  Got: Y` / `⏱ TLE`
6. Append summary line to session `README.md`

---

## Hint Rules

- **NEVER** show Tier 2 unless user explicitly asks or has been stuck 30+ min
- **Tier 1** = gentle nudge, no algorithm name, no spoilers
- **Tier 2** = concrete technique + time/space complexity

---

## Question Bank (28 problems seeded)

Pre-seeded to target weak areas:

| Category | Count | Examples |
|----------|-------|---------|
| Dynamic Programming | 10 | Climbing Stairs, Coin Change, LIS, Edit Distance, Burst Balloons, Partition DP |
| Backtracking | 6 | Subsets, Permutations, N-Queens, Word Search, Sudoku Solver, Combination Sum |
| Advanced DS (Heaps / Tries / DSU / Seg Tree) | 8 | Kth Largest, Merge K Lists, Implement Trie, Word Search II, Accounts Merge, Range Sum Mutable |
| Mixed Multi-DS | 4 | LRU Cache, Sliding Window Maximum, Min Stack, Design Twitter |

---

## Implementation Phases

### Phase 1 — Scaffold ✅ DONE
- `README.md`, `SETUP.md`, `WORKFLOW.md`, `problem_selection.md`, `CLAUDE.md`
- `templates/problem.cpp.template`, `templates/testcases.template`, `templates/session_readme.template`
- `coding_patterns.md` — pre-filled with Harshita's weak areas and patterns reference (DP/Trie/DSU/Monotonic Stack C++ snippets)
- `question_bank.md` — 28 problems seeded
- `session_log.md` — header only
- `git init` + initial commit

### Phase 2 — Core Scripts ✅ DONE
- `scripts/fetch_problem.py` — LC (GraphQL), CF (API + cloudscraper), CSES (scrape), stdin, discover-cf
- `scripts/run_tests.py` — compile C++17, test runner, UNORDERED/FLOAT/DRIVER flags, README append
- `scripts/timer.py` — countdown with alerts at 30/15/10/5/2/1 min
- `include/bits/stdc++.h` — macOS shim so `#include <bits/stdc++.h>` works on Apple Clang

### Phase 3 — Session Management Scripts ✅ DONE
- `scripts/new_session.py` — creates session dir, problem stubs, README, session_summary.md, optional timer
- `scripts/select_repeat.py` — weighted candidate scoring, outputs top-3
- `scripts/update_patterns.py` — auto-extracts confidence + test results, updates dashboard, progress note, session log

### Phase 4 — First Real Session ✅ DONE
- Fetched CF 2143/C "Max Tree" (rating 1300, tags: constructive, graphs, greedy) via `--discover-cf` + CF API
- Verified `update_patterns.py` end-to-end: dashboard updated correctly (Graphs + Greedy → 3.0 comfort)
- All scripts committed and pushed to GitHub

---

## What Still Needs Testing

| Item | Status | Test command |
|------|--------|-------------|
| LeetCode fetch | Untested | `python3 scripts/fetch_problem.py --url https://leetcode.com/problems/two-sum/ --session sessions/test --slot p1` |
| CSES fetch | Untested | `python3 scripts/fetch_problem.py --url https://cses.fi/problemset/task/1068 --session sessions/test --slot p1` |
| `run_tests.py` end-to-end | Untested | Write a solution, add tests, run `python3 scripts/run_tests.py <file>.cpp` |
| `new_session.py` interactive | Untested | Run without `--no-timer` in a real terminal |
| `timer.py` | Untested | `python3 scripts/timer.py 5` |
| Full contest end-to-end | Untested | `new_session → fetch 5 problems → write solutions → run tests → update_patterns` |

---

## Known Issues

| Issue | Severity | Status |
|-------|----------|--------|
| CF HTML scraping blocked by Cloudflare | Medium | Handled — graceful fallback with placeholder, user pastes statement manually |
| LeetCode fetch untested | Medium | Test next session |
| CSES fetch untested | Low | Test next session |
| `git config user.name/email` not set | Cosmetic | Run: `git config --global user.name "Harshita"` and `git config --global user.email "you@example.com"` |

---

## GitHub

**Repo:** https://github.com/Harshi-itaSinha/dsa-tutor (private)

Post-session commit workflow:
```bash
git add sessions/ coding_patterns.md question_bank.md session_log.md
git commit -m "Session: YYYY-MM-DD <type> — X/5 solved"
git push
```

---

## Next Steps (Recommended Order)

1. **Run your first full contest session** — `python3 scripts/new_session.py --type contest --company <Company>`
2. **Test LeetCode fetch** on a real problem
3. **Test `run_tests.py`** by writing a trivial solution and running it
4. **Set git identity** — `git config --global user.name "Harshita"`
5. After a few sessions, **run `--weekly-report`** to see pattern trends
