# 📦 Quantum Optimization for Distributed Order Management

**WISER × Nestlé Global Quantum+AI Program 2026**
Team: Entangled Minds 

## The problem, in one line

Nestlé has 8 warehouses. Sometimes an order's assigned warehouse is out of
stock. Do you ship it from somewhere else instead — and if so, from where?

That sounds easy for one order. It's a genuinely hard puzzle for hundreds
of them at once, all competing for the same trucks, shelves, and loading
docks. This repo is our attempt at solving it — on Nestlé's real 2024 data,
not a toy example.

## What we actually did

We didn't just pick one method and call it done. We tried it five-ish
different ways and let the numbers argue it out:

- **Do nothing** (baseline) → only 14% of stuck orders ship
- **Greedy, first-come-first-served** → 89% ship, but shipping costs balloon
- **Exact math (ILP solver)** → the provably best answer: $447,822 in value recovered
- **Five "quantum-inspired" algorithms**, benchmarked head to head — turns out plain old Steepest Descent beat fancier quantum-flavored methods, landing at 99.2% of the optimal answer in 0.08 seconds
- **An actual quantum computer circuit (QAOA)**, built and run on a small slice of the problem — because the full problem is way too big for today's quantum hardware or simulators (744+ variables vs. the ~6-10 qubits we could realistically run)

The honest finding: exact math and simple local search win today. Real
quantum computing isn't there yet for a problem this size — but we proved
the approach works at small scale, which is the whole point of a challenge
like this.

## Numbers, if you want them

| Method | Objective ($) | Fill Rate |
|---|---|---|
| Do nothing | 229,995 | 14% |
| Greedy | 412,060 | 89% |
| **Exact solver (ILP)** | **447,822** | 53% |
| Steepest Descent (quantum-inspired) | 444,071 | 53%, in 0.08s |
| Real QAOA circuit (6 qubits) | — | 25% off optimal |

Full breakdown, methodology, and why fill rate alone is a misleading metric
→ `package/Technical_Report.docx`.

## Poking around this repo

\```
package/
├── DOM_Solution_Pipeline.ipynb   ← the whole thing, already run once
├── real_data.py                  ← loads & documents the real data
├── baseline_pulp.py              ← baselines + exact solver
├── qubo_qaoa.py                  ← quantum encoding
├── compare_quantum_algos.py      ← the 5-algorithm face-off
├── qaoa_small_subset.py          ← real quantum circuit, small scale
├── data_dictionary.md            ← what every column in the data means
├── task3_formulation.md          ← the math, spelled out
├── task5_scaling_analysis.md     ← what breaks at bigger scale, and how to fix it
├── Technical_Report.docx
├── Task1_Business_Technical_Summary.docx
└── Planner_View.docx             ← plain-English summary for non-technical readers
\```

## Run it yourself

\```bash
pip install pulp dimod dwave-samplers qiskit qiskit-aer pandas numpy scipy jupyter
\```

Drop your own `DOM-data` folder (from the WISER workspace) inside `package/`,
open `DOM_Solution_Pipeline.ipynb`, and hit Restart & Run All.

> The real data pack isn't in this repo — it's `.gitignore`d on purpose,
> per WISER/Nestlé's data-handling rules. Only aggregate results and
> anonymized IDs are shown publicly anywhere in here.

## Deadline

Submitted for the WISER Quantum+AI Program 2026, due August 7.
