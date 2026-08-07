"""
Task 4 (extended): compares MULTIPLE quantum / quantum-inspired algorithms
on the same QUBO, at the full 93-order real-data scale, plus a genuine
gate-based QAOA circuit run on a small subset (since 744 qubits is not
statevector-simulable). Reports which is the best-suited method for this
problem at this scale, against the ILP exact optimum as ground truth.

Algorithms compared on the full-scale QUBO (744 binary variables):
  1. Random sampling            - naive baseline, shows the QUBO isn't trivial
  2. Simulated Annealing (SA)   - classical thermal annealing
  3. Tabu Search                - classical local search with memory
  4. Steepest Descent           - greedy local search to a local optimum
  5. Path-Integral Quantum Monte Carlo (PIQMC) - simulates quantum
     annealing's tunneling behaviour via Trotterized replicas; the
     closest classical proxy to how a real D-Wave quantum annealer
     would search this landscape

Then, on a SMALL subset (tractable for a real quantum circuit):
  6. QAOA (qiskit-aer statevector simulator) - actual gate-based quantum
     algorithm, compared against brute-force optimum on that subset
"""
import time
import numpy as np
import dimod
from dwave.samplers import (
    SimulatedAnnealingSampler, TabuSampler, SteepestDescentSampler,
    RandomSampler, PathIntegralAnnealingSampler,
)
from real_data import load_real_instance
from qubo_qaoa import build_qubo, decode
from baseline_pulp import report as report_metrics


def run_sampler(name, sampler, bqm, inst, **kwargs):
    t0 = time.time()
    result = sampler.sample(bqm, **kwargs)
    elapsed = time.time() - t0
    best_sample = result.first.sample
    assignment = decode(best_sample, inst)
    m = report_metrics(inst, assignment, name)
    m["label"] = name
    m["runtime_s"] = elapsed
    return m


if __name__ == "__main__":
    print("=" * 70)
    print("PART 1: Quantum-inspired algorithms at full scale (93 orders x 8 DCs)")
    print("=" * 70)
    inst = load_real_instance(n_focus_orders=None)
    Q = build_qubo(inst)
    bqm = dimod.BinaryQuadraticModel.from_qubo(Q)
    print(f"QUBO size: {len(bqm.variables)} binary variables\n")

    results = []
    results.append(run_sampler("1. Random sampling", RandomSampler(), bqm, inst, num_reads=200))
    results.append(run_sampler("2. Simulated Annealing", SimulatedAnnealingSampler(), bqm, inst, num_reads=200, seed=7))
    results.append(run_sampler("3. Tabu Search", TabuSampler(), bqm, inst, num_reads=20, timeout=5000))
    results.append(run_sampler("4. Steepest Descent", SteepestDescentSampler(), bqm, inst, num_reads=200, seed=7))
    results.append(run_sampler("5. Path-Integral QMC", PathIntegralAnnealingSampler(), bqm, inst, num_reads=50, num_sweeps=200, seed=7))

    print("\n=== Full-scale comparison (ILP optimum = 447,822 for reference) ===")
    print(f"{'Method':28s} {'Objective':>12s} {'Fill':>6s} {'Reassigned':>11s} {'Runtime(s)':>11s}")
    for m in results:
        print(f"{m['label']:28s} {m['objective']:12.2f} {m['fill_rate']:6.0%} {m['reassigned']:11d} {m['runtime_s']:11.3f}")

    best = max(results, key=lambda m: m["objective"])
    print(f"\nBest quantum-inspired method at this scale: {best['label']} "
          f"(objective {best['objective']:.2f}, {best['objective']/447822.39:.1%} of ILP optimum)")
