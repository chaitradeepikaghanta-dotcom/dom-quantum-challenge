# Task 5 — Scaling and Noise Analysis

## 5.1 How variables/qubits grow with problem size

In our reduced formulation (§3.2), one binary variable `x_{o,d}` exists
per (order, candidate DC) pair, so variable count = `|orders| × |DCs|`.
The real data pack gives us several concrete growth points:

| Scope | Orders | DCs | Variables (qubits) | What we actually ran |
|---|---|---|---|---|
| Toy demo (initial synthetic test) | 6 | 3 | 18 | ✅ ILP + QUBO/SA |
| QAOA-feasible subset | 3 | 2 | **6** | ✅ real gate-based QAOA circuit + brute force |
| Tractable single-SKU subset | 93 | 8 | **744** | ✅ ILP, 2 baselines, 5 quantum-inspired algorithms |
| All single-SKU focus orders | 93 | 8 | 744 | (same as above — this is the full single-SKU set) |
| **All real focus orders** (incl. multi-SKU) | 359 | 8 | 2,872 | Not run — see §5.2 |
| All open orders in the pack | 614 | 8 | 4,912 | Not run |
| Full order-SKU-DC-date grid (Nestlé's original `Cases_osdp` model) | 25,193 lines | 8 | ~10 dates | **≈ 2,000,000+** | Not run — intractable at this scale |

Growth is **linear in orders × DCs** for our reduced model, but the
original Nestlé formulation adds a SKU dimension and a date dimension to
every case-level variable (`Cases_osdp`, `Casepick_osdp`, `Palletpick_osdp`),
so the *real* production-scale problem grows closer to
`orders × DCs × SKUs × dates` — multiple orders of magnitude larger than
what we solved.

## 5.2 How each approach performs as the problem grows

**Exact ILP (PuLP/CBC):** solved our 744-variable instance in under 2
seconds — trivial at this scale. But ILP runtime for general binary
optimization grows worst-case exponentially with variable count; ILP
solvers manage this in practice via branch-and-bound pruning, which works
well when the LP relaxation is tight (ours mostly is, since our
constraints are simple capacity/assignment bounds). We'd expect this to
degrade noticeably once the multi-SKU/date dimensions are reintroduced,
since the constraint structure (case-pick/pallet-pick conversion, dock
capacity per date) is far less sparse.

**Quantum-inspired heuristics (§4, `compare_quantum_algos.py`):** at
744 variables, runtime ranged from 0.08s (Steepest Descent) to 100s (Tabu
Search) — all still practical. These are local-search methods, so their
runtime scales roughly with variable count × iterations rather than
exploding combinatorially, which is exactly why they're the fallback when
exact solving becomes too slow. The trade-off we observed directly:
Steepest Descent and Tabu stayed close to the ILP optimum (99.2% / 98.1%),
while Simulated Annealing and Path-Integral QMC drifted further (82.6% /
80.1%) despite similar runtimes — thermal/tunneling-style exploration
doesn't automatically win on a landscape this shaped.

**Real QAOA (gate-based, `qaoa_small_subset.py`):** only tractable up to
about 6 qubits on a statevector simulator in our environment (2ⁿ state
growth). Even at that toy scale, shallow-depth QAOA (p=2) landed 25.1%
off the brute-force optimum. This is the central noise/scaling limitation
for this problem: **near-term quantum hardware and simulators cannot yet
touch the qubit counts this problem needs** (744 today, millions at full
production scale), and even at feasible sizes, shallow circuits don't yet
match classical local search. This directly reflects the "noisy quantum
hardware vs. simulators" trade-off flagged in Task 1.

**Robustness:** the quantum-inspired methods are stochastic (different
random seeds can shift the result a few percent), while ILP is
deterministic. For a planner-facing tool, that argues for either running
several seeds and taking the best (as `compare_quantum_algos.py` does with
multiple reads), or defaulting to the deterministic classical method
(Steepest Descent/ILP) and reserving quantum-inspired search for cases
where problem size makes exact solving too slow.

## 5.3 Proposed scalability improvement: batching by DC-cluster

Given the linear-in-orders×DCs growth of variables, the clearest lever is
**batching focus orders into smaller, near-independent sub-problems**
before solving:

1. Group focus orders by their **candidate DC set overlap** — orders that
   share no plausible alternate DC (e.g. because of geography/shipping
   cost) don't need to compete in the same optimization run.
2. Solve each batch independently (ILP for small batches, quantum-inspired
   for larger ones), then merge results.
3. This turns one 2,872-variable problem (all 359 real focus orders) into,
   e.g., 8 smaller problems of a few hundred variables each — each
   comfortably ILP-solvable, and each small enough that even a real QAOA
   run becomes plausible on a handful of orders at a time.

The risk this introduces: orders in different batches can no longer
compete for the same shared inventory if their DC sets actually do
overlap, so batch boundaries need to be chosen conservatively (e.g. by
DC-region clusters with genuinely disjoint candidate sets) or paired with
a light second pass that checks for missed reassignment opportunities
across batch boundaries.

## 5.4 Summary

| Dimension | Current scale (real subset) | Full production scale | Gap |
|---|---|---|---|
| Variables | 744 | ~2.9k (focus orders) → millions (full multi-SKU/date model) | 4x – 1000x+ |
| Best method today | Steepest Descent (99.2% of optimum, 0.08s) | Unknown — needs batching to stay tractable | — |
| Real QAOA feasible | Up to ~6-10 qubits | Not remotely close | Orders of magnitude |

Batching is the practical near-term path to closing this gap without
waiting for either classical solvers or quantum hardware to catch up on
their own.
