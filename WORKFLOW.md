# Session Workflows

## Contest Session

### Starting
```bash
python3 scripts/new_session.py --type contest --company Google
```
This creates `sessions/YYYY-MM-DD_Google/` with 5 problem files and a timer prompt.

**What the script does:**
1. Creates the session directory
2. Reads `coding_patterns.md` to identify current weaknesses
3. Selects 4 new problems (1 easy, 2 medium on weak topics, 1 hard)
4. Runs `select_repeat.py` to pick p5 (the repeat)
5. Creates `p1..p5` `.cpp` and `_tests.txt` files from templates
6. Creates `README.md` and `session_summary.md` stubs
7. Asks if you want to start the timer

### During the Contest
1. Open `p1_<slug>.cpp` in your editor
2. Read the problem statement in the comment header
3. **Do NOT scroll past the HINTS section until stuck**
4. When stuck > 15 min → read `[TIER 1 HINT]` only
5. When stuck > 30 min → read `[TIER 2 HINT]`
6. Write your solution below `// ===== YOUR SOLUTION BELOW =====`
7. Test manually with the examples in the comment
8. Run automated tests:
   ```bash
   python3 scripts/run_tests.py sessions/YYYY-MM-DD_Google/p1_<slug>.cpp
   ```
9. Fix failures, re-run, then move to p2

### After the Contest (do this immediately)
1. Fill in `YOUR NOTES` section at the bottom of each problem file:
   - Approach you tried
   - Time/space complexity
   - Edge cases you missed
   - Confidence rating (1–5)

2. Fill in `sessions/YYYY-MM-DD_Google/session_summary.md`:
   - What went well
   - What went wrong
   - Hints used and when
   - Key takeaways

3. Update patterns:
   ```bash
   python3 scripts/update_patterns.py --session sessions/YYYY-MM-DD_Google
   ```

4. Add a row to `session_log.md`

5. Commit:
   ```bash
   git add .
   git commit -m "Session: YYYY-MM-DD Google contest — X/5 solved"
   git push
   ```

---

## Practice Session

```bash
python3 scripts/new_session.py --type practice --topic dp
```

Same flow as contest, except:
- No company name, no timer by default (optional)
- 3–5 problems instead of 5
- No repeat problem unless you want one
- Focused on one or two topics

---

## Doubt Session

```bash
python3 scripts/new_session.py --type doubt --topic "segment tree"
```

Creates `sessions/YYYY-MM-DD_doubt/`:
- `doubt_segment_tree.md` — structured explanation file
- Optionally a single practice problem to verify understanding

**Doubt file format:**
```
## CONFUSION POINT
What exactly confused you?

## CANONICAL EXPLANATION
The correct explanation with examples

## WORKED EXAMPLE
Step-by-step walkthrough of a concrete case

## TEST QUESTION
A small problem to confirm you understood
```

After the doubt session, add the insight to `coding_patterns.md` under the relevant pattern.

---

## Asking for Hints Mid-Contest

Tell Claude:
- `"tier 1 hint for p2"` → you get the nudge, no spoilers
- `"tier 2 hint for p2"` → you get the concrete approach
- `"I've been stuck for 45 min, show me the approach for p3"` → tier 2

Claude will **never** show tier 2 unless you explicitly ask or have already received tier 1.

---

## Adding a Problem You Found Yourself

```bash
python3 scripts/fetch_problem.py --url https://leetcode.com/problems/some-problem/ \
  --session sessions/YYYY-MM-DD_practice --slot p3
```

Or paste manually:
```bash
python3 scripts/fetch_problem.py --stdin --session sessions/YYYY-MM-DD_practice --slot p3
```

---

## Requesting a Progress Report

Tell Claude: `"give me a progress report"` — it will read `coding_patterns.md` and `session_log.md` and produce a summary of your growth, current weaknesses, and recommended focus areas.

---

## Running Tests

```bash
# Single problem
python3 scripts/run_tests.py sessions/2026-04-05_Google/p1_two_sum.cpp

# All problems in a session
python3 scripts/run_tests.py sessions/2026-04-05_Google/
```

---

## Handling a Problem You Could Not Finish

- Set status in YOUR NOTES: `Confidence: 1`
- In `question_bank.md`, mark the problem `needs-review`
- It will be weighted heavily for repeat selection
- Don't delete or skip the test run — partial solutions still count

---

## Post-Session Git Checklist

```bash
git status                          # see what changed
git add sessions/ coding_patterns.md question_bank.md session_log.md
git commit -m "Session: YYYY-MM-DD <type> — brief note"
git push
```
