# Coding Patterns Tracker

_Last updated: 2026-04-05 | Sessions completed: 0 | Problems solved: 0_

---

## SUMMARY DASHBOARD

| Pattern | Comfort (1–5) | Attempted | Solved | Avg Time | Priority |
|---------|---------------|-----------|--------|----------|----------|
| Arrays / Two Pointers | ? | 0 | 0 | — | — |
| Sliding Window | ? | 0 | 0 | — | — |
| Binary Search | ? | 0 | 0 | — | — |
| Linked Lists | ? | 0 | 0 | — | — |
| Stacks & Queues | ? | 0 | 0 | — | — |
| Trees / BFS / DFS | ? | 0 | 0 | — | — |
| Graphs | ? | 0 | 0 | — | — |
| Dynamic Programming | 1 | 0 | 0 | — | HIGH |
| Backtracking | 1 | 0 | 0 | — | HIGH |
| Heaps / Priority Queue | ? | 0 | 0 | — | HIGH |
| Tries | 1 | 0 | 0 | — | HIGH |
| Union-Find (DSU) | ? | 0 | 0 | — | — |
| Segment Tree / BIT | 1 | 0 | 0 | — | HIGH |
| Mixed Multi-DS | 1 | 0 | 0 | — | HIGH |
| Greedy | ? | 0 | 0 | — | — |
| Bit Manipulation | ? | 0 | 0 | — | — |
| Strings | ? | 0 | 0 | — | — |

_Comfort scale: 1 = can't start independently, 2 = need hints, 3 = can solve with effort, 4 = comfortable, 5 = fluent_
_Priority: HIGH = active weakness, update after 5+ problems in this topic_

---

## RECURRING MISTAKES

_Format: Date | Problem | Mistake | Category | Fix / Lesson_

| Date | Problem | Mistake | Category | Fix / Lesson |
|------|---------|---------|----------|--------------|

---

## STRENGTHS

_Fill this in after your first 3–5 sessions_

---

## WEAKNESSES (priority order for practice)

1. **Dynamic Programming** — Cannot identify state space independently; unsure of recurrence direction
2. **Backtracking** — Pruning applied too late; does not define invariants before recursing
3. **Advanced Data Structures** (Tries, Segment Trees, Heaps, DSU) — Rarely implemented from scratch; interface shaky
4. **Mixed Multi-DS problems** — Struggle when a problem combines e.g. stack + hash map + deque together

---

## PATTERNS REFERENCE

### Dynamic Programming — Checklist
```
1. Is it asking for optimal value, count, or existence? (not construction)
2. Define dp[i] = answer for subproblem ending at / using first i elements
3. Recurrence: dp[i] depends on dp[i-1]? dp[i-k]? dp[i][j-1]?
4. Base case: dp[0] or dp[empty state]?
5. Order: left-to-right usually; 2D usually row-by-row
6. Space optimization: rolling array if only dp[i-1] is needed
```

Common DP patterns:
- **Linear DP**: LIS, Coin Change, Climbing Stairs
- **0/1 Knapsack**: dp[i][w] = max value using first i items with capacity w
- **Unbounded Knapsack**: same but items can be reused; inner loop direction flips
- **Interval DP**: dp[l][r] = answer for subarray [l, r]; fill by length
- **Partition DP**: split array at every k; dp[i] = best split ending at i
- **String DP**: Edit Distance, LCS; dp[i][j] operates on prefixes

### Backtracking — Template
```cpp
void backtrack(state, candidates, result) {
    if (goal_reached(state)) {
        result.push_back(state);
        return;
    }
    for each choice in candidates:
        if (is_valid(choice, state)):      // pruning here
            apply(choice, state);
            backtrack(state, candidates, result);
            undo(choice, state);           // restore state
}
```
Key: define the pruning condition BEFORE writing the recursive call.

### Tries — Implementation
```cpp
struct TrieNode {
    TrieNode* children[26] = {};
    bool is_end = false;
};

void insert(TrieNode* root, string& word) {
    TrieNode* cur = root;
    for (char c : word) {
        int i = c - 'a';
        if (!cur->children[i]) cur->children[i] = new TrieNode();
        cur = cur->children[i];
    }
    cur->is_end = true;
}

bool search(TrieNode* root, string& word) {
    TrieNode* cur = root;
    for (char c : word) {
        int i = c - 'a';
        if (!cur->children[i]) return false;
        cur = cur->children[i];
    }
    return cur->is_end;
}
```

### Union-Find (DSU)
```cpp
struct DSU {
    vector<int> parent, rank_;
    DSU(int n) : parent(n), rank_(n, 0) { iota(parent.begin(), parent.end(), 0); }
    int find(int x) { return parent[x] == x ? x : parent[x] = find(parent[x]); }
    bool unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;
        if (rank_[a] < rank_[b]) swap(a, b);
        parent[b] = a;
        if (rank_[a] == rank_[b]) rank_[a]++;
        return true;
    }
};
```

### Monotonic Stack — When to Use
- "Next greater/smaller element" → monotonic stack
- "Largest rectangle in histogram" → maintain stack of indices
- Deque for sliding window maximum → monotonic deque

### Sliding Window (Variable)
```
left = 0
for right in range(n):
    window.add(arr[right])
    while window_violates_condition:
        window.remove(arr[left])
        left++
    update_answer
```

### Binary Search on Answer
```
When to use: "minimize the maximum" / "smallest X where f(X) is true"
lo = min_possible, hi = max_possible
while lo < hi:
    mid = (lo + hi) / 2
    if check(mid): hi = mid
    else: lo = mid + 1
```

---

## TOPIC HISTORY
_Updated by update_patterns.py after each session_
_Format: topic: [QID@session-dir, ...]_

dp: []
backtracking: []
tries: []
segment-tree: []
heap: []
dsu: []
mixed-ds: []
arrays: []
graphs: []
trees: []

---

## PROGRESS NOTES
_Newest first — add after each session_

### 2026-04-05 — Initial Setup
- Project initialized. Weak areas: DP, Backtracking, Advanced DS, Mixed multi-DS.
- Question bank seeded with 28 problems.
- First session not yet run.
