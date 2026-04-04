# Question Bank

_Total problems: 28 | Last updated: 2026-04-05_
_Seeded topics: DP (10), Backtracking (6), Advanced DS (8), Mixed multi-DS (4)_

---

## Quick Index

| ID   | Title | Platform | Tags | Diff | Status | Last Used | Times Used | Repeat Eligible |
|------|-------|----------|------|------|--------|-----------|------------|-----------------|
| Q001 | Climbing Stairs | LC | dp, linear-dp | E | unseen | — | 0 | never-used |
| Q002 | House Robber | LC | dp, linear-dp | M | unseen | — | 0 | never-used |
| Q003 | Coin Change | LC | dp, unbounded-knapsack | M | unseen | — | 0 | never-used |
| Q004 | Longest Increasing Subsequence | LC | dp, binary-search | M | unseen | — | 0 | never-used |
| Q005 | Edit Distance | LC | dp, string-dp | H | unseen | — | 0 | never-used |
| Q006 | Partition Equal Subset Sum | LC | dp, 0-1-knapsack | M | unseen | — | 0 | never-used |
| Q007 | Burst Balloons | LC | dp, interval-dp | H | unseen | — | 0 | never-used |
| Q008 | Palindrome Partitioning II | LC | dp, interval-dp | H | unseen | — | 0 | never-used |
| Q009 | Decode Ways | LC | dp, linear-dp | M | unseen | — | 0 | never-used |
| Q010 | Unique Paths II | LC | dp, grid-dp | M | unseen | — | 0 | never-used |
| Q011 | Subsets | LC | backtracking | M | unseen | — | 0 | never-used |
| Q012 | Permutations | LC | backtracking | M | unseen | — | 0 | never-used |
| Q013 | Combination Sum | LC | backtracking | M | unseen | — | 0 | never-used |
| Q014 | N-Queens | LC | backtracking | H | unseen | — | 0 | never-used |
| Q015 | Word Search | LC | backtracking, dfs | M | unseen | — | 0 | never-used |
| Q016 | Sudoku Solver | LC | backtracking | H | unseen | — | 0 | never-used |
| Q017 | Kth Largest Element | LC | heap | M | unseen | — | 0 | never-used |
| Q018 | Merge K Sorted Lists | LC | heap, linked-list | H | unseen | — | 0 | never-used |
| Q019 | Find Median from Data Stream | LC | heap | H | unseen | — | 0 | never-used |
| Q020 | Implement Trie | LC | trie | M | unseen | — | 0 | never-used |
| Q021 | Word Search II | LC | trie, backtracking | H | unseen | — | 0 | never-used |
| Q022 | Number of Islands | LC | dsu, bfs | M | unseen | — | 0 | never-used |
| Q023 | Accounts Merge | LC | dsu | M | unseen | — | 0 | never-used |
| Q024 | Range Sum Query — Mutable | LC | segment-tree | M | unseen | — | 0 | never-used |
| Q025 | LRU Cache | LC | mixed-ds, hash-map, dll | M | unseen | — | 0 | never-used |
| Q026 | Sliding Window Maximum | LC | mixed-ds, monotonic-deque | H | unseen | — | 0 | never-used |
| Q027 | Min Stack | LC | mixed-ds, stack | E | unseen | — | 0 | never-used |
| Q028 | Design Twitter | LC | mixed-ds, heap, hash-map | M | unseen | — | 0 | never-used |

---

## Problem Details

### Q001 — Climbing Stairs
- URL: https://leetcode.com/problems/climbing-stairs/
- Tags: dp, linear-dp
- Difficulty: Easy
- Notes: Classic intro to DP. Fibonacci recurrence. Use as p1 warm-up for first few sessions.
- Repeat weight: LOW (too easy once solved)

### Q002 — House Robber
- URL: https://leetcode.com/problems/house-robber/
- Tags: dp, linear-dp
- Difficulty: Medium
- Notes: dp[i] = max(dp[i-1], dp[i-2] + nums[i]). Good for linear DP fluency.
- Repeat weight: MEDIUM

### Q003 — Coin Change
- URL: https://leetcode.com/problems/coin-change/
- Tags: dp, unbounded-knapsack
- Difficulty: Medium
- Notes: Classic knapsack. Common confusion: direction of inner loop (bottom-up left-to-right for unbounded).
- Repeat weight: HIGH

### Q004 — Longest Increasing Subsequence
- URL: https://leetcode.com/problems/longest-increasing-subsequence/
- Tags: dp, binary-search
- Difficulty: Medium
- Notes: O(n²) DP is easy; O(n log n) with patience sort / binary search is the key insight.
- Repeat weight: HIGH

### Q005 — Edit Distance
- URL: https://leetcode.com/problems/edit-distance/
- Tags: dp, string-dp
- Difficulty: Hard
- Notes: dp[i][j] = min ops to convert word1[0..i] to word2[0..j]. Three transitions: insert, delete, replace.
- Repeat weight: HIGH

### Q006 — Partition Equal Subset Sum
- URL: https://leetcode.com/problems/partition-equal-subset-sum/
- Tags: dp, 0-1-knapsack
- Difficulty: Medium
- Notes: Reduce to 0/1 knapsack with target = total/2. Key: iterate capacity backwards.
- Repeat weight: HIGH

### Q007 — Burst Balloons
- URL: https://leetcode.com/problems/burst-balloons/
- Tags: dp, interval-dp
- Difficulty: Hard
- Notes: Think about which balloon is burst LAST in a range, not first. dp[l][r] = max coins.
- Repeat weight: HIGH

### Q008 — Palindrome Partitioning II
- URL: https://leetcode.com/problems/palindrome-partitioning-ii/
- Tags: dp, interval-dp, string-dp
- Difficulty: Hard
- Notes: Two DP passes: precompute palindrome check, then min cuts. Good interval DP practice.
- Repeat weight: HIGH

### Q009 — Decode Ways
- URL: https://leetcode.com/problems/decode-ways/
- Tags: dp, linear-dp
- Difficulty: Medium
- Notes: Careful edge cases with '0'. dp[i] depends on dp[i-1] and dp[i-2].
- Repeat weight: MEDIUM

### Q010 — Unique Paths II
- URL: https://leetcode.com/problems/unique-paths-ii/
- Tags: dp, grid-dp
- Difficulty: Medium
- Notes: 2D DP on grid with obstacles. dp[i][j] = 0 if grid[i][j] is obstacle.
- Repeat weight: MEDIUM

### Q011 — Subsets
- URL: https://leetcode.com/problems/subsets/
- Tags: backtracking
- Difficulty: Medium
- Notes: Simplest backtracking pattern. Choose / don't choose each element.
- Repeat weight: LOW

### Q012 — Permutations
- URL: https://leetcode.com/problems/permutations/
- Tags: backtracking
- Difficulty: Medium
- Notes: Swap-based or used[] array approach. All elements distinct.
- Repeat weight: LOW

### Q013 — Combination Sum
- URL: https://leetcode.com/problems/combination-sum/
- Tags: backtracking
- Difficulty: Medium
- Notes: Elements can repeat (unbounded). Start index prevents duplicate combos.
- Repeat weight: MEDIUM

### Q014 — N-Queens
- URL: https://leetcode.com/problems/n-queens/
- Tags: backtracking
- Difficulty: Hard
- Notes: Track attacked columns, diagonals (/), anti-diagonals (\) with sets. Pruning is critical.
- Repeat weight: HIGH

### Q015 — Word Search
- URL: https://leetcode.com/problems/word-search/
- Tags: backtracking, dfs
- Difficulty: Medium
- Notes: DFS on grid with visited state. Restore grid cell after backtracking (mark/unmark).
- Repeat weight: MEDIUM

### Q016 — Sudoku Solver
- URL: https://leetcode.com/problems/sudoku-solver/
- Tags: backtracking
- Difficulty: Hard
- Notes: Classic CSP. Row/col/box constraint sets. Try digits 1–9, prune immediately on conflict.
- Repeat weight: HIGH

### Q017 — Kth Largest Element in Array
- URL: https://leetcode.com/problems/kth-largest-element-in-an-array/
- Tags: heap, quickselect
- Difficulty: Medium
- Notes: Min-heap of size k, or quickselect O(n) average. Know both.
- Repeat weight: LOW

### Q018 — Merge K Sorted Lists
- URL: https://leetcode.com/problems/merge-k-sorted-lists/
- Tags: heap, linked-list
- Difficulty: Hard
- Notes: Min-heap of (val, list_index, node). Push next node from same list after popping.
- Repeat weight: MEDIUM

### Q019 — Find Median from Data Stream
- URL: https://leetcode.com/problems/find-median-from-data-stream/
- Tags: heap
- Difficulty: Hard
- Notes: Max-heap (left half) + min-heap (right half). Rebalance after every insert so sizes differ by at most 1.
- Repeat weight: HIGH

### Q020 — Implement Trie (Prefix Tree)
- URL: https://leetcode.com/problems/implement-trie-prefix-tree/
- Tags: trie
- Difficulty: Medium
- Notes: Foundational trie implementation. 26-child array per node. Insert, search, startsWith.
- Repeat weight: HIGH

### Q021 — Word Search II
- URL: https://leetcode.com/problems/word-search-ii/
- Tags: trie, backtracking
- Difficulty: Hard
- Notes: Build trie from word list. DFS on board checks trie nodes. Prune dead trie branches.
- Repeat weight: HIGH

### Q022 — Number of Islands
- URL: https://leetcode.com/problems/number-of-islands/
- Tags: dsu, bfs, dfs
- Difficulty: Medium
- Notes: BFS/DFS flood fill is easy. For DSU practice, union adjacent '1' cells and count roots.
- Repeat weight: LOW (if BFS already fluent)

### Q023 — Accounts Merge
- URL: https://leetcode.com/problems/accounts-merge/
- Tags: dsu, hash-map
- Difficulty: Medium
- Notes: DSU where nodes are emails. Union all emails in the same account. Group by root.
- Repeat weight: HIGH

### Q024 — Range Sum Query — Mutable
- URL: https://leetcode.com/problems/range-sum-query-mutable/
- Tags: segment-tree, bit
- Difficulty: Medium
- Notes: Implement segment tree or Binary Indexed Tree (Fenwick) from scratch. Update O(log n), query O(log n).
- Repeat weight: HIGH

### Q025 — LRU Cache
- URL: https://leetcode.com/problems/lru-cache/
- Tags: mixed-ds, hash-map, doubly-linked-list
- Difficulty: Medium
- Notes: Hash map (key → node) + doubly linked list (order). Move to front on get/put. Remove from tail on evict.
- Repeat weight: HIGH

### Q026 — Sliding Window Maximum
- URL: https://leetcode.com/problems/sliding-window-maximum/
- Tags: mixed-ds, monotonic-deque
- Difficulty: Hard
- Notes: Monotonic decreasing deque of indices. Front = max of current window. Pop front if out of window.
- Repeat weight: HIGH

### Q027 — Min Stack
- URL: https://leetcode.com/problems/min-stack/
- Tags: mixed-ds, stack
- Difficulty: Easy
- Notes: Two stacks: main + min-tracker. Push to min-stack only when new min ≤ current min.
- Repeat weight: LOW

### Q028 — Design Twitter
- URL: https://leetcode.com/problems/design-twitter/
- Tags: mixed-ds, heap, hash-map
- Difficulty: Medium
- Notes: Hash map (user → tweets list) + hash map (user → followees set). getNewsFeed = merge-k-sorted via heap.
- Repeat weight: MEDIUM
