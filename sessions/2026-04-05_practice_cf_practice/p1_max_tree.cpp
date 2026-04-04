// =============================================================================
// PROBLEM: Max Tree
// SOURCE:  https://codeforces.com/problemset/problem/2143/C  |  Platform: CF
// ADDED:   2026-04-05  |  TAGS: constructive algorithms, dfs and similar, graphs, greedy
// DIFFICULTY: CF-Medium (1300)  |  COMPANY: Codeforces
// REPEAT: NO
// =============================================================================
//
// PROBLEM STATEMENT:
// -----------------------------------------------------------------------
// You are given a tree consisting of n vertices, numbered from 1 to
// n. Each of the n - 1 edges is associated with two non-negative
// integers x and y.
// 
// Consider a permutation^∗ p of the integers 1 through
// n, where p_i represents the value assigned to vertex i.
// 
// For an edge (u, v), such that u < v with associated values x
// and y, its contribution is defined as follows: 
// { x        if  p_u > p_v;  y        otherwise.
// 
// The value of the permutation is the sum of the contributions from all edges.
// 
// Your task is to find any permutation p that maximizes this total value.
// 
// ^∗A permutation of length n is an array consisting of
// n distinct integers from 1 to n in arbitrary order. For
// example, [2,3,1,5,4] is a permutation, but [1,2,2] is not a
// permutation (2 appears twice in the array), and [1,3,4] is also not
// a permutation (n=3 but there is 4 in the array).
//
// Input:
//   Each test contains multiple test cases. The first line contains the number of
// test cases t (1 <= t <= 10^4). The description of the test cases
// follows.
// 
// The first line contains a single integer n (2 <= n <= 2 *
// 10^5) — the number of vertices in the tree.
// 
// Each of the next n - 1 lines contains four integers u, v,
// x, and y (1 <= u < v <= n, 1 <= x, y <= 10^9) —
// describing an edge between vertices u and v with associated values
// x and y. It is guarranteed that the given edges form a tree.
// 
// It is guaranteed that the sum of n over all test cases does not exceed
// 2 * 10^5.
//
// Output:
//   For each test case, you must output a permutation p of the integers
// 1 through n that maximizes the total value as defined in the
// problem. If there are multiple answers, you can print any of them.
//
// Constraints:
//   (see problem — check time/memory limits on Codeforces)
//
// Examples:
//   (see problem)
//
// -----------------------------------------------------------------------
//
// [TIER 1 HINT — Nudge, no spoilers. Read after 15+ min stuck]:
// -----------------------------------------------------------------------
//   TODO — to be filled by Claude before the session starts
//
// [TIER 2 HINT — Concrete approach. Read after 30+ min stuck]:
// -----------------------------------------------------------------------
//   TODO — to be filled by Claude before the session starts
//   Time complexity: ?  |  Space complexity: ?
//
// -----------------------------------------------------------------------
//
// YOUR NOTES (fill after solving):
// -----------------------------------------------------------------------
//   Approach tried:
//
//   Time complexity:
//   Space complexity:
//   Edge cases missed:
//   Confidence (1-5):
//
// =============================================================================

#include <bits/stdc++.h>
using namespace std;
#define ll long long
#define pii pair<int,int>
#define vi vector<int>
#define vvi vector<vector<int>>

// ===== YOUR SOLUTION BELOW =====

class Solution {
public:

};

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    // Write your manual test driver here (optional).
    // Automated tests are run via: python3 scripts/run_tests.py <this-file>

    return 0;
}
