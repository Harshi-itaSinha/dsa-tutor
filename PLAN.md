# DSA Tutor — Project Plan

This file documents the full plan discussed and built for this project.

---

## Goal

Build a fully self-contained, file-based DSA tutoring system that:
- Simulates company OA contests (Google, Amazon, etc.) with 5 timed problems
- Tracks weaknesses and growth through a central `coding_patterns.md`
- Auto-generates and runs test cases against C++ solutions
- Uses weakness data to intelligently select and repeat problems
- Learns what mistakes you make during coding, not just after
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
        ├── p1_<slug>.attempts   — auto-logged history of every test run (Phase 6)
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

## How the System Learns Your Mistakes — Intelligence Layers

The system is designed in three progressively smarter layers for tracking mistakes.

### What "manual input" gives you (Layer 1 — current)
You fill in two fields after each problem:
- `Edge cases missed:` — what you forgot
- `Confidence (1-5):` — how sure you were

`update_patterns.py` reads these and automatically:
- Updates comfort score per topic (rolling average)
- Flags the edge case in the session report
- Keeps the topic's priority HIGH until comfort rises

**Limitation:** You have to correctly self-diagnose your own mistakes. If you don't notice a pattern, it doesn't get recorded.

### What attempt logging gives you (Layer 2 — Phase 6)
Every time you run `run_tests.py`, it appends a timestamped line to `p1_slug.attempts`:
```
2026-04-05 14:03  run 1/3 — 0/5 passed  failed: [2,3,4,5]
2026-04-05 14:21  run 2/3 — 3/5 passed  failed: [4,5]
2026-04-05 14:35  run 3/3 — 5/5 passed
```
`update_patterns.py` reads these files and computes:
- **Struggle score**: how many runs before passing (3 runs = struggled)
- **Which tests you consistently fail**: test 4 failed twice → likely an edge case pattern
- **Time between runs**: large gaps = got stuck

This is fully automatic — zero effort from you. The system sees your entire journey, not just your final answer.

### What failure pattern detection gives you (Layer 3 — Phase 7)
When a test fails, the runner already has `Got: Y, Expected: X`. We can auto-classify:

| Got vs Expected | Likely mistake category |
|----------------|------------------------|
| `Y = X ± 1` on multiple tests | `off-by-one` |
| Empty output | `base-case-missing` |
| TLE on large input | `wrong-complexity` |
| Correct on examples, wrong on edge cases only | `edge-case-blindness` |
| Wrong sign / overflow on large numbers | `overflow` |

Over many sessions, `update_patterns.py` surfaces: *"In the last 10 sessions, 4 of your 6 failures were `off-by-one` errors in binary search problems."*

---

## Implementation Phases

### Phase 1 — Scaffold + Manual Tracking ✅ DONE
**Goal:** A working system where you can run sessions and manually record what went wrong.

- [x] `README.md`, `SETUP.md`, `WORKFLOW.md`, `problem_selection.md`, `CLAUDE.md`
- [x] `templates/` — problem.cpp.template, testcases.template, session_readme.template
- [x] `coding_patterns.md` — pre-filled with weak areas + patterns reference (DP/Trie/DSU/Monotonic Stack C++ snippets)
- [x] `question_bank.md` — 28 problems seeded (DP×10, Backtracking×6, Advanced DS×8, Mixed×4)
- [x] `session_log.md` — header initialized
- [x] `scripts/fetch_problem.py` — LC (GraphQL), CF (API + cloudscraper), CSES, stdin, --discover-cf
- [x] `scripts/run_tests.py` — compile C++17, test runner, UNORDERED/FLOAT flags, README append
- [x] `scripts/timer.py` — countdown with interval alerts
- [x] `scripts/new_session.py` — creates full session directory with stubs
- [x] `scripts/select_repeat.py` — weighted repeat candidate scoring
- [x] `scripts/update_patterns.py` — reads confidence + edge cases, updates dashboard, appends progress note
- [x] `include/bits/stdc++.h` — macOS shim for Apple Clang
- [x] First real session tested: CF 2143/C Max Tree, dashboard updated correctly
- [x] All committed and pushed to GitHub

**Manual inputs required from you each session:**
1. After solving: fill `Edge cases missed:` and `Confidence (1-5):` in the problem file
2. After session: fill `session_summary.md` (what went well, what went wrong, takeaways)
3. Run `python3 scripts/update_patterns.py --session sessions/<dir>` — rest is automatic

---

### Phase 2 — End-to-End Testing 🔲 TODO
**Goal:** Verify every script works with real problems before relying on them in a contest.

- [ ] Test LeetCode fetch end-to-end with a real URL
- [ ] Test CSES fetch end-to-end
- [ ] Test `run_tests.py` with a written C++ solution (passing + failing cases)
- [ ] Test `new_session.py` in interactive mode (timer prompt)
- [ ] Test `timer.py` countdown
- [ ] Run a full contest session start-to-finish:
  `new_session → fetch 5 problems → write solutions → run_tests → update_patterns → commit`

---

### Phase 3 — Attempt Logger (Zero-Effort Struggle Tracking) 🔲 TODO
**Goal:** `run_tests.py` records every test run automatically so the system knows how hard you struggled, with no extra effort from you.

**What to build:**
- After every `run_tests.py` run, append a line to `p1_slug.attempts`:
  ```
  2026-04-05 14:03  run 1 — 0/5 passed  failed_tests: [2, 3, 4, 5]
  2026-04-05 14:21  run 2 — 3/5 passed  failed_tests: [4, 5]
  2026-04-05 14:35  run 3 — 5/5 passed
  ```
- Update `update_patterns.py` to read `.attempts` files and compute:
  - **Runs to pass** per problem (1 = confident, 4+ = struggled)
  - **Tests that repeatedly failed** across runs (signals a specific blind spot)
  - **Struggle score** = (runs to pass × time span) — feeds into dashboard alongside comfort score

**New field in SUMMARY DASHBOARD:**
```
| Pattern | Comfort | Attempted | Solved | Avg Runs to Pass | Avg Time | Priority |
```
`Avg Runs to Pass > 3` on a topic → problem is you don't just lack knowledge, you make implementation mistakes even when you know the approach.

---

### Phase 4 — Failure Pattern Detection (Auto-Classify Mistakes) 🔲 TODO
**Goal:** When tests fail, the system classifies what type of mistake caused the failure — automatically, without you having to diagnose it.

**What to build:**
- In `run_tests.py`, after a FAIL: compare `Got` vs `Expected` and emit a `mistake_hint`:
  - `Got = Expected ± 1` → `off-by-one`
  - `Got` is empty string → `base-case-missing`
  - TLE → `wrong-complexity`
  - `Got` matches on test 1 (basic), wrong on test 3 (edge) → `edge-case-blindness`
  - `Got` has very large/negative number → `overflow`
- Log the classification into the `.attempts` file alongside the failed test numbers
- `update_patterns.py` aggregates mistake categories across all sessions and adds a new section to `coding_patterns.md`:

```markdown
## MISTAKE PATTERNS (auto-detected, last 30 sessions)
| Category | Count | Most recent | Topics most affected |
|----------|-------|-------------|---------------------|
| off-by-one | 8 | 2026-04-10 | Binary Search, DP |
| edge-case-blindness | 5 | 2026-04-08 | Backtracking |
| overflow | 3 | 2026-04-06 | DP |
```

This tells you not just *that* you struggle with DP — but *how* you fail at it.

---

### Phase 5 — Claude Code Review Integration 🔲 TODO
**Goal:** At end of session, Claude reads your solution code and automatically identifies mistake patterns that the file-level tracking can't see (wrong algorithm choice, missed pruning, poor variable naming that led to logic errors).

**What to build:**
- A post-session prompt template: "Review my solution for p2 and fill in `Edge cases missed:` and suggest a row for `RECURRING MISTAKES`"
- Claude reads the `.cpp` solution, the test failures from `.attempts`, and produces:
  - A filled `Edge cases missed:` line
  - A categorized mistake entry ready to paste into `RECURRING MISTAKES`
  - One-line takeaway for `coding_patterns.md`
- Over time, Claude cross-references past mistakes: *"You made the same off-by-one error in binary search that you made 3 sessions ago in Q004."*

**This layer requires no new scripts** — it's a workflow change: you paste your code to Claude at the end of each session instead of self-diagnosing.

---

## Current Status Summary

| Phase | Status | What it gives you |
|-------|--------|-------------------|
| Phase 1 — Manual Tracking | ✅ DONE | Working system, you fill in mistakes yourself |
| Phase 2 — End-to-End Testing | 🔲 TODO | Confidence that all scripts work in a real contest |
| Phase 3 — Attempt Logger | 🔲 TODO | Automatic struggle tracking, zero extra effort |
| Phase 4 — Failure Pattern Detection | 🔲 TODO | Auto-classify mistake types (off-by-one, overflow, etc.) |
| Phase 5 — Claude Code Review | 🔲 TODO | Deepest insight, cross-session mistake pattern memory |

---

## What Still Needs Testing (Phase 2 checklist)

| Item | Test command |
|------|-------------|
| LeetCode fetch | `python3 scripts/fetch_problem.py --url https://leetcode.com/problems/two-sum/ --session sessions/test_lc --slot p1` |
| CSES fetch | `python3 scripts/fetch_problem.py --url https://cses.fi/problemset/task/1068 --session sessions/test_cses --slot p1` |
| `run_tests.py` with passing solution | Write trivial correct C++, run against test file |
| `run_tests.py` with failing solution | Write wrong solution, verify FAIL output shows input/expected/got |
| `new_session.py` interactive | Run in terminal without `--no-timer` |
| `timer.py` | `python3 scripts/timer.py 5` |
| Full contest end-to-end | `new_session → fetch 5 → solve → test → update_patterns → commit` |

---

## Known Issues

| Issue | Severity | Status |
|-------|----------|--------|
| CF HTML scraping blocked by Cloudflare | Medium | Handled — graceful fallback, user pastes statement manually |
| LeetCode fetch untested | Medium | Phase 2 |
| CSES fetch untested | Low | Phase 2 |
| `git config user.name/email` not set | Cosmetic | Run: `git config --global user.name "Harshita"` |

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

## Immediate Next Steps

1. **Complete Phase 2** — run through the testing checklist above, fix any issues found
2. **Run your first real contest session** — `python3 scripts/new_session.py --type contest --company <Company>`
3. **Set git identity** — `git config --global user.name "Harshita" && git config --global user.email "you@email.com"`
4. After a few sessions → **build Phase 3** (attempt logger) — biggest gain for least effort
