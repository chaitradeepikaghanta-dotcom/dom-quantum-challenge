"""
Task 4 (extended), Part 2: a hand-built QAOA circuit (qiskit-algorithms
0.4.0 is incompatible with the installed qiskit 2.x primitives interface,
so QAOA is implemented directly here -- standard textbook construction).
Run on a SMALL subset (6 qubits) where statevector simulation and
brute-force ground truth are both feasible, unlike the full 744-qubit
instance.
"""
import itertools
import numpy as np
from scipy.optimize import minimize
from qiskit.circuit import QuantumCircuit
from qiskit_aer import AerSimulator
import dimod

from real_data import load_real_instance
from qubo_qaoa import build_qubo, decode
from baseline_pulp import report as report_metrics


def qubo_to_ising(bqm):
    """QUBO (x in {0,1}) -> Ising (z in {-1,+1}) via x = (1-z)/2."""
    variables = list(bqm.variables)
    idx = {v: i for i, v in enumerate(variables)}
    n = len(variables)
    h = np.zeros(n)
    J = {}
    offset = bqm.offset
    for v, bias in bqm.linear.items():
        i = idx[v]
        h[i] += -bias / 2
        offset += bias / 2
    for (u, v), bias in bqm.quadratic.items():
        i, j = idx[u], idx[v]
        J[(i, j)] = J.get((i, j), 0) + bias / 4
        h[i] += -bias / 4
        h[j] += -bias / 4
        offset += bias / 4
    return h, J, offset, variables


def qaoa_circuit(n, h, J, gammas, betas):
    qc = QuantumCircuit(n)
    qc.h(range(n))
    for gamma, beta in zip(gammas, betas):
        for i in range(n):
            if h[i] != 0:
                qc.rz(2 * gamma * h[i], i)
        for (i, j), coeff in J.items():
            if coeff != 0:
                qc.cx(i, j)
                qc.rz(2 * gamma * coeff, j)
                qc.cx(i, j)
        for i in range(n):
            qc.rx(2 * beta, i)
    qc.measure_all()
    return qc


def expected_cost(counts, h, J, offset):
    total_shots = sum(counts.values())
    exp = 0.0
    for bitstring, count in counts.items():
        z = np.array([1 - 2 * int(b) for b in bitstring[::-1]])  # qiskit bit order
        energy = offset + sum(h[i] * z[i] for i in range(len(h)))
        energy += sum(coeff * z[i] * z[j] for (i, j), coeff in J.items())
        exp += energy * count / total_shots
    return exp


def run_qaoa(h, J, offset, reps=2, shots=2048, seed=7):
    n = len(h)
    backend = AerSimulator(seed_simulator=seed)

    def objective(params):
        gammas, betas = params[:reps], params[reps:]
        qc = qaoa_circuit(n, h, J, gammas, betas)
        result = backend.run(qc, shots=shots).result()
        counts = result.get_counts()
        return expected_cost(counts, h, J, offset)

    x0 = np.random.default_rng(seed).uniform(0, np.pi, size=2 * reps)
    res = minimize(objective, x0, method="COBYLA", options={"maxiter": 150})

    gammas, betas = res.x[:reps], res.x[reps:]
    qc = qaoa_circuit(n, h, J, gammas, betas)
    counts = backend.run(qc, shots=shots).result().get_counts()
    best_bitstring = max(counts, key=counts.get)
    return best_bitstring, res.fun


def brute_force(bqm):
    variables = list(bqm.variables)
    best_energy, best_sample = None, None
    for bits in itertools.product([0, 1], repeat=len(variables)):
        sample = dict(zip(variables, bits))
        e = bqm.energy(sample)
        if best_energy is None or e < best_energy:
            best_energy, best_sample = e, sample
    return best_sample, best_energy


if __name__ == "__main__":
    full_inst = load_real_instance(n_focus_orders=None)
    orders_sub = full_inst["orders"][:3]
    dcs_sub = full_inst["dcs"][:2]
    skus_sub = sorted(set(full_inst["order_sku"][o] for o in orders_sub))

    inst = {
        "orders": orders_sub, "dcs": dcs_sub, "skus": skus_sub,
        "order_sku": {o: full_inst["order_sku"][o] for o in orders_sub},
        "default_dc": {o: full_inst["default_dc"][o] for o in orders_sub},
        "value": {o: full_inst["value"][o] for o in orders_sub},
        "ship_cost": {(o, d): full_inst["ship_cost"][(o, d)] for o in orders_sub for d in dcs_sub},
        "penalty": {o: full_inst["penalty"][o] for o in orders_sub},
        "inventory": {(d, s): full_inst["inventory"][(d, s)] for d in dcs_sub for s in skus_sub},
        "throughput": {d: full_inst["throughput"][d] for d in dcs_sub},
    }

    Q = build_qubo(inst)
    bqm = dimod.BinaryQuadraticModel.from_qubo(Q)
    n = len(bqm.variables)
    print(f"Small subset: {len(orders_sub)} orders x {len(dcs_sub)} DCs = {n} qubits\n")

    bf_sample, bf_energy = brute_force(bqm)
    bf_assignment = decode(bf_sample, inst)
    bf_metrics = report_metrics(inst, bf_assignment, "Brute-force optimum (ground truth)")

    h, J, offset, variables = qubo_to_ising(bqm)
    best_bitstring, qaoa_energy_est = run_qaoa(h, J, offset, reps=2, shots=2048)

    qaoa_sample = {variables[i]: int(bit) for i, bit in enumerate(best_bitstring[::-1])}
    qaoa_assignment = decode(qaoa_sample, inst)
    qaoa_metrics = report_metrics(inst, qaoa_assignment, "QAOA (hand-built circuit, p=2, qiskit-aer)")

    print("\n=== Small-subset comparison (6-qubit real quantum circuit) ===")
    print(f"{'Method':45s} {'Objective':>10s} {'Fill':>6s}")
    print(f"{'Brute-force optimum':45s} {bf_metrics['objective']:10.2f} {bf_metrics['fill_rate']:6.0%}")
    print(f"{'QAOA (real circuit, p=2, qiskit-aer)':45s} {qaoa_metrics['objective']:10.2f} {qaoa_metrics['fill_rate']:6.0%}")
    gap = (bf_metrics['objective'] - qaoa_metrics['objective']) / max(abs(bf_metrics['objective']), 1)
    print(f"\nQAOA optimality gap: {gap:.1%}")
