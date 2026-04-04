# Problem Selection Algorithm

## For New Problems (4 per contest)

Problems are chosen from `question_bank.md` filtered to `status: unseen` or `status: needs-review`.

### Slot Allocation Per Contest

| Slot | Difficulty | Criteria |
|------|-----------|----------|
| p1 | Easy | warm-up; not from a current weakness topic |
| p2 | Medium | targets current weakness #1 (see coding_patterns.md) |
| p3 | Medium | targets current weakness #2 or mixed-DS problems |
| p4 | Hard | most challenging; targets a weak area or introduces a new pattern |

### Scoring for New Problem Selection

```
score(Q) = freshness * weakness_boost * variety_bonus

freshness:
  status == "unseen"        → 1.0
  status == "needs-review"  → 0.8   (seen but needs another attempt)

weakness_boost:
  Q.tags intersects top-2 weaknesses in coding_patterns.md → 2.0
  Q.tags intersects top-3 weaknesses                       → 1.5
  Q.tags intersects a strength                             → 0.5
  otherwise                                                → 1.0

variety_bonus:
  Q.tags NOT used in the previous session → 1.2
  Q.tags used in previous session         → 0.8
```

Problems are ranked by score. Claude selects the top match per slot, then presents the 4 chosen problems with reasoning so you can override.

---

## For the Repeat Problem (p5 in every contest)

### Eligibility Rules

A problem is eligible for repeat if ALL of the following are true:

1. It has been used in a previous session (status = `solved` or `attempted`)
2. It was NOT used in the immediately preceding session (by date)
3. It was NOT used as a repeat problem in the immediately preceding contest
4. It has not been used in the last 2 sessions (recency buffer)

### Scoring for Repeat Selection

```
score(Q) = base * recency * weakness_boost

base:
  status == "needs-review"  → 3.0
  status == "attempted"     → 2.0
  status == "solved"        → 1.0

recency (sessions since last use):
  > 10 sessions ago → 1.5
  4–10 sessions ago → 1.0
  2–3 sessions ago  → 0.8

weakness_boost:
  tags match a current weakness → 2.0
  tags match a strength         → 0.7
  otherwise                     → 1.0
```

`select_repeat.py` outputs the top-3 candidates with scores. Claude picks one contextually (e.g., avoids repeating a topic if p2/p3 already cover it).

### Override

You can always manually pick the repeat:
```
"use Q003 (Coin Change) as the repeat today"
```

### "Too Easy" Flag

If you feel a problem is permanently below your level, mark it in `question_bank.md`:
```
- Repeat eligible: never (too easy)
```
It will be excluded from all future repeat selection.

---

## First 28 Problems — Seeding Logic

Weak areas provided at setup: DP, Backtracking, Advanced Data Structures, Mixed multi-DS problems.

| Category | Count | Reasoning |
|----------|-------|-----------|
| DP | 10 | Primary weakness; large variety of DP subtypes |
| Backtracking | 6 | Secondary weakness; needs pruning practice |
| Advanced DS (Heaps, Tries, DSU, Seg Tree) | 8 | Rarely implemented from scratch |
| Mixed multi-DS | 4 | Explicit gap mentioned; LRU, sliding window, monotonic stack combos |

Problems are graded Easy (2), Medium (5), Hard (3) within each category to allow warm-up and progression.

---

## Adding Problems to the Bank Mid-Session

Any problem Claude writes, fetches, or you request gets automatically added to `question_bank.md` with:
- Status: `unseen` (if not yet attempted) or `attempted`/`solved` (if done in this session)
- Tags derived from problem content
- Source URL or `custom`

---

## Progress-Based Rebalancing

After every 5 sessions, `update_patterns.py` checks if any topic's `Comfort` score in the dashboard has risen above 3.5. If so, it automatically reduces the weakness_boost for that topic and may suggest adding new topics to the queue.
