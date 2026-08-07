"""
Task 3/4: QUBO encoding of the DOM problem for quantum / quantum-inspired
solving (QAOA-style), solved here with simulated annealing (a classical
quantum-inspired proxy — see notes at the bottom on the actual QAOA circuit).

--- Encoding ---
Binary variable per (order, DC) pair, same as the ILP: x[o,d] in {0,1}.
QAOA/QUBO solvers need an UNCONSTRAINED objective, so hard constraints
become quadratic PENALTY terms added to the cost function instead of
explicit inequality constraints:

  1. "at most one DC per order":  A * sum_o (sum_d x[o,d] - 1)^2   [only if forced to =1;
     since partial non-assignment is allowed, we instead penalize
     *multiple* assignments: A * sum_o sum_{d<d'} x[o,d]*x[o,d']]
  2. inventory capacity per (DC, SKU): B * sum_{d,s} ( sum_{o in s} x[o,d] - inv[d,s] )_+^2
     (approximated below as a quadratic over-capacity penalty)
  3. throughput cap per DC: C * (sum_o x[o,d] - throughput[d])_+^2  (approximated similarly)

Objective (to MINIMIZE, so we negate the ILP's maximization terms):
  H = -sum_{o,d}(value[o]-ship_cost[o,d]) x[o,d]
      + sum_o penalty[o] * (1 - sum_d x[o,d])       <- kept linear, already unconstrained-friendly
      + A * one-DC-violation terms
      + B * inventory-violation terms (soft)
      + C * throughput-violation terms (soft)

This gives a QUBO matrix Q such that H(x) = x^T Q x (+ constant), which is
exactly the form QAOA optimizes: encode Q as a cost Hamiltonian H_C over
one qubit per (order, DC) pair, alternate with a mixer Hamiltonian H_M
(sum of X_i), and optimize circuit angles (beta, gamma) to minimize <H_C>.
"""
import dimod
import neal
from real_data import load_real_instance as load_instance


def build_qubo(inst, A=None, B=None, C=None):
    orders, dcs, skus = inst["orders"], inst["dcs"], inst["skus"]
    value, ship_cost, penalty = inst["value"], inst["ship_cost"], inst["penalty"]
    inventory, throughput, order_sku = inst["inventory"], inst["throughput"], inst["order_sku"]

    # scale constraint penalty weights relative to the objective's own magnitude
    # (fixed constants tuned for a small synthetic instance don't transfer to
    # real revenue figures in the hundreds of thousands)
    typical_term = max(value.values()) if value else 1
    if A is None:
        A = 2 * typical_term
    if B is None:
        B = 2 * typical_term
    if C is None:
        C = 2 * typical_term

    Q = {}  # dict[(var_i, var_j)] = coefficient, dimod's sparse QUBO format
    var = lambda o, d: f"x_{o}_{d}"

    def add(i, j, val):
        key = (i, j) if i <= j else (j, i)
        Q[key] = Q.get(key, 0) + val

    # --- linear reward/cost term: -(value - ship_cost) per (o,d), plus penalty bookkeeping ---
    for o in orders:
        for d in dcs:
            v = var(o, d)
            # negative because QUBO minimizes; we want to maximize (value-ship_cost) and
            # avoid the penalty (penalty[o] is incurred only when order stays unassigned,
            # i.e. contributes -penalty[o]*x[o,d] as a "reward" for assigning)
            add(v, v, -(value[o] - ship_cost[(o, d)]) - penalty[o])

    # --- constraint A: at most one DC per order -> penalize any pair d<d' both selected ---
    for o in orders:
        for i, d1 in enumerate(dcs):
            for d2 in dcs[i + 1:]:
                add(var(o, d1), var(o, d2), 2 * A)

    # --- constraint B: inventory capacity per (DC, SKU) ---
    # NOTE: a naive (sum x - cap)^2 penalty is symmetric -- it penalizes being
    # UNDER capacity just as much as OVER it, which wrongly discourages valid,
    # low-utilization assignments. We use a one-sided approximation instead:
    #   - if cap == 0: hard-exclude every assignment to that (DC,SKU) (large linear penalty)
    #   - if cap >= 1: only penalize pairwise co-selection beyond what cap allows
    #     (exact for cap==1 "at most one"; an approximation for cap>1 with group
    #     sizes above cap -- a known simplification, see Task 5 / feasibility-repair notes)
    for d in dcs:
        for s in skus:
            group = [o for o in orders if order_sku[o] == s]
            cap = inventory[(d, s)]
            if cap == 0:
                for o in group:
                    add(var(o, d), var(o, d), B)
            elif len(group) > cap:
                for i, o1 in enumerate(group):
                    for o2 in group[i + 1:]:
                        add(var(o1, d), var(o2, d), B)

    # --- constraint C: throughput cap per DC, same one-sided approach ---
    for d in dcs:
        cap = throughput[d]
        if cap == 0:
            for o in orders:
                add(var(o, d), var(o, d), C)
        elif len(orders) > cap:
            for i, o1 in enumerate(orders):
                for o2 in orders[i + 1:]:
                    add(var(o1, d), var(o2, d), C)

    return Q


def decode(sample, inst):
    orders, dcs = inst["orders"], inst["dcs"]
    assignment = {}
    for o in orders:
        chosen = [d for d in dcs if sample.get(f"x_{o}_{d}", 0) == 1]
        assignment[o] = chosen[0] if len(chosen) == 1 else None  # None if 0 or >1 (constraint violated)
    return assignment


if __name__ == "__main__":
    inst = load_instance(n_focus_orders=None)
    Q = build_qubo(inst)
    print(f"QUBO built: {len(inst['orders']) * len(inst['dcs'])} binary variables, "
          f"{len(Q)} nonzero (linear+quadratic) terms")

    bqm = dimod.BinaryQuadraticModel.from_qubo(Q)

    sampler = neal.SimulatedAnnealingSampler()
    result = sampler.sample(bqm, num_reads=200, seed=7)
    best = result.first.sample

    assignment = decode(best, inst)
    n_unfulfilled = sum(1 for v in assignment.values() if v is None)
    print(f"\nSample solved: {len(assignment) - n_unfulfilled}/{len(assignment)} orders assigned "
          f"(per-order assignment details omitted from output for public-repo privacy)")

    from baseline_pulp import report
    report(inst, assignment, "Quantum-inspired (simulated annealing on QUBO)")

    print("""
--- Mapping this QUBO onto an actual QAOA circuit ---
  * One qubit per (order, DC) pair -> here, {n} qubits for {no} orders x {nd} DCs.
  * Cost Hamiltonian H_C: replace each x_i with (I - Z_i)/2 in the QUBO expression
    above to get a sum of Z_i and Z_i*Z_j Pauli terms (this is what
    qiskit-optimization's QuadraticProgram -> QAOAAnsatz conversion does automatically).
  * Mixer Hamiltonian H_M = sum_i X_i (standard QAOA mixer).
  * Circuit: p layers of exp(-i*gamma*H_C) then exp(-i*beta*H_M), angles tuned
    by a classical optimizer (COBYLA/SPSA) to minimize <H_C>.
  * IMPORTANT: at {n} qubits this is NOT statevector-simulator-feasible
    (2^{n} states is far beyond reach; practical statevector simulation tops
    out around 25-30 qubits). The simulated-annealing result above is a
    classical quantum-inspired proxy standing in for QAOA at this scale --
    an actual QAOA run would need either a much smaller batch (a handful of
    orders x DCs) or a real QPU / tensor-network simulator. See Task 5 for
    why batching/column reduction is the practical path to a real quantum
    experiment on this problem.
""".format(n=len(inst["orders"]) * len(inst["dcs"]), no=len(inst["orders"]), nd=len(inst["dcs"])))
