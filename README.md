# DSA Tutor

A self-contained, file-based DSA practice system that simulates company coding assessments, tracks your patterns and growth, and adapts problem selection to target your weaknesses.

## Quick Start

```bash
# Start a contest session
python3 scripts/new_session.py --type contest --company Google

# Start a practice session
python3 scripts/new_session.py --type practice --topic dp

# Start a doubt session
python3 scripts/new_session.py --type doubt --topic backtracking

# Run tests against your solution
python3 scripts/run_tests.py sessions/2026-04-05_Google/p1_two_sum.cpp

# Fetch a problem by URL
python3 scripts/fetch_problem.py --url https://leetcode.com/problems/two-sum/

# Fetch a problem by pasting
python3 scripts/fetch_problem.py --stdin

# Start countdown timer (in minutes)
python3 scripts/timer.py 90

# Update patterns after a session
python3 scripts/update_patterns.py --session sessions/2026-04-05_Google
```

## Session Types

| Type | What it is | Problems |
|------|-----------|----------|
| `contest` | Company OA simulation | 5 (4 new + 1 repeat) |
| `practice` | Topic-focused drill | 3–5 |
| `doubt` | Clarify a concept | 1 + explanation doc |

## Key Files

| File | Purpose |
|------|---------|
| `coding_patterns.md` | Your patterns tracker — strengths, weaknesses, mistakes, progress |
| `question_bank.md` | All problems with status, tags, history |
| `session_log.md` | One-line log per session |
| `WORKFLOW.md` | Step-by-step instructions for every session type |
| `SETUP.md` | One-time setup and dependencies |

## Directory Layout

```
sessions/
  YYYY-MM-DD_<Company|practice|doubt>/
    README.md               # session metadata + test results
    p1_<slug>.cpp           # problem + hints + your solution
    p1_<slug>_tests.txt     # generated test cases
    p5_REPEAT_<slug>.cpp    # repeat problem (always p5 in contests)
    session_summary.md      # your post-session debrief

templates/       # file skeletons used by new_session.py
scripts/         # all automation scripts
archive/         # snapshots of coding_patterns.md before major rewrites
```

## Supported Problem Sources

- LeetCode URLs (`https://leetcode.com/problems/...`)
- Codeforces URLs (`https://codeforces.com/contest/.../problem/...`)
- CSES URLs (`https://cses.fi/problemset/task/...`)
- Manual paste (`--stdin`)

## Setup

See `SETUP.md` for one-time installation.
