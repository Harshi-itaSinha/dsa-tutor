# Setup Guide

## Prerequisites

### 1. Python 3 and pip

```bash
python3 --version   # should be 3.8+
pip3 --version
```

### 2. C++ Compiler

```bash
g++ --version   # should be g++ 11+ for C++17 support
```

On macOS, if not installed:
```bash
xcode-select --install
```

### 3. Python Dependencies

```bash
pip3 install requests beautifulsoup4 html2text
```

These are used by `fetch_problem.py` to scrape LeetCode, Codeforces, and CSES.

### 4. Git

```bash
git --version
```

## One-Time Initialization

From the `dsa-tutor/` directory:

```bash
git init
git add .
git commit -m "Initial DSA tutor setup"
```

Then connect to your GitHub repo (create a private repo named `dsa-tutor` on github.com first):

```bash
git remote add origin https://github.com/<your-username>/dsa-tutor.git
git push -u origin main
```

## Seeding the Question Bank

Before your first session, seed the question bank with 28 problems targeting your weak areas.
This is already done — see `question_bank.md`.

## Configuration

You can tweak behavior at the top of each script:

| Script | Config variables |
|--------|-----------------|
| `run_tests.py` | `TLE_SECONDS` (default 2), `MEMORY_LIMIT_MB` (default 512) |
| `new_session.py` | `DEFAULT_DURATION_MIN` (default 90), `DEFAULT_LANG` (default `cpp`) |
| `select_repeat.py` | Scoring weights at the top of the file |

## Troubleshooting

**LeetCode fetch fails / returns empty:**
- LeetCode rate-limits the GraphQL endpoint. Wait 30 seconds and retry.
- Premium problems require session cookies. Use `--stdin` instead.

**Codeforces fetch has garbled math:**
- MathJax formulas are stripped imperfectly. The fetcher adds a `# MATH_CLEANUP_NEEDED` comment. Fix manually.

**`g++` not found on macOS:**
- Run `xcode-select --install` and try again.

**Permission denied on scripts:**
- `chmod +x scripts/*.py`
