"""
Task 4 (classical exact baseline): binary optimization model for DOM,
solved with PuLP/CBC.

Decision variable: x[o,d] = 1 if order o is assigned to DC d.

Objective (maximize):
    sum_{o,d} (value[o] - ship_cost[o,d]) * x[o,d]
    - sum_o penalty[o] * (1 - sum_d x[o,d])

Constraints:
    - each order assigned to at most one DC
    - per-DC, per-SKU inventory limit
    - per-DC throughput (order count) cap
"""
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpBinary, PULP_CBC_CMD, LpStatus
from real_data import load_real_instance as load_instance


def solve(inst):
    orders, dcs, skus = inst["orders"], inst["dcs"], inst["skus"]
    value, ship_cost, penalty = inst["value"], inst["ship_cost"], inst["penalty"]
    inventory, throughput, order_sku = inst["inventory"], inst["throughput"], inst["order_sku"]

    prob = LpProblem("DOM_baseline", LpMaximize)

    x = {(o, d): LpVariable(f"x_{o}_{d}", cat=LpBinary) for o in orders for d in dcs}

    # objective
    fulfil_term = lpSum((value[o] - ship_cost[(o, d)]) * x[(o, d)] for o in orders for d in dcs)
    penalty_term = lpSum(penalty[o] * (1 - lpSum(x[(o, d)] for d in dcs)) for o in orders)
    prob += fulfil_term - penalty_term

    # each order to at most one DC
    for o in orders:
        prob += lpSum(x[(o, d)] for d in dcs) <= 1

    # inventory limits per DC/SKU
    for d in dcs:
        for s in skus:
            orders_needing_s = [o for o in orders if order_sku[o] == s]
            prob += lpSum(x[(o, d)] for o in orders_needing_s) <= inventory[(d, s)]

    # throughput cap per DC
    for d in dcs:
        prob += lpSum(x[(o, d)] for o in orders) <= throughput[d]

    prob.solve(PULP_CBC_CMD(msg=False))

    assignment = {o: next((d for d in dcs if x[(o, d)].value() > 0.5), None) for o in orders}
    return prob, assignment


def report(inst, assignment, label):
    orders = inst["orders"]
    value, ship_cost, penalty = inst["value"], inst["ship_cost"], inst["penalty"]

    fulfilled = [o for o in orders if assignment[o] is not None]
    fill_rate = len(fulfilled) / len(orders)
    reassigned = [o for o in fulfilled if assignment[o] != inst["default_dc"][o]]
    total_shipping = sum(ship_cost[(o, assignment[o])] for o in fulfilled)
    total_value = sum(value[o] for o in fulfilled)
    total_penalty = sum(penalty[o] for o in orders if assignment[o] is None)
    objective = total_value - total_shipping - total_penalty

    print(f"\n--- {label} ---")
    print(f"Objective value:     {objective:.2f}")
    print(f"Fill rate:           {fill_rate:.0%} ({len(fulfilled)}/{len(orders)})")
    print(f"Orders reassigned:   {len(reassigned)}")
    print(f"Total shipping cost: {total_shipping:.2f}")
    print(f"Total penalty cost:  {total_penalty:.2f}")
    # NOTE: per-order assignment details (order IDs -> DC) are intentionally
    # NOT printed here to keep public-repo output at the aggregate-metrics
    # level per the challenge's data privacy rules. The full `assignment`
    # dict is still returned/available in-memory for anyone running this
    # locally with their own authorized data pack access.
    return {"objective": objective, "fill_rate": fill_rate, "reassigned": len(reassigned),
            "shipping": total_shipping, "penalty": total_penalty}


def default_assignment_baseline(inst):
    """Baseline 1: everyone stays at their default DC (feasibility not checked)."""
    orders, skus, dcs = inst["orders"], inst["skus"], inst["dcs"]
    inventory, order_sku, throughput = inst["inventory"], inst["order_sku"], inst["throughput"]
    remaining_inv = dict(inventory)
    remaining_cap = dict(throughput)
    assignment = {}
    for o in orders:
        d = inst["default_dc"][o]
        s = order_sku[o]
        if remaining_inv[(d, s)] > 0 and remaining_cap[d] > 0:
            assignment[o] = d
            remaining_inv[(d, s)] -= 1
            remaining_cap[d] -= 1
        else:
            assignment[o] = None
    return assignment


def greedy_baseline(inst):
    """Baseline 2: sort orders by value desc, assign to cheapest DC with capacity."""
    orders, dcs, skus = inst["orders"], inst["dcs"], inst["skus"]
    inventory, throughput, order_sku, ship_cost, value = (
        inst["inventory"], inst["throughput"], inst["order_sku"], inst["ship_cost"], inst["value"]
    )
    remaining_inv = dict(inventory)
    remaining_cap = dict(throughput)
    assignment = {}
    for o in sorted(orders, key=lambda o: -value[o]):
        s = order_sku[o]
        candidates = [d for d in dcs if remaining_inv[(d, s)] > 0 and remaining_cap[d] > 0]
        if not candidates:
            assignment[o] = None
            continue
        best_d = min(candidates, key=lambda d: ship_cost[(o, d)])
        assignment[o] = best_d
        remaining_inv[(best_d, s)] -= 1
        remaining_cap[best_d] -= 1
    return assignment


if __name__ == "__main__":
    inst = load_instance(n_focus_orders=None)

    a1 = default_assignment_baseline(inst)
    m1 = report(inst, a1, "Baseline 1: Default-assignment")

    a2 = greedy_baseline(inst)
    m2 = report(inst, a2, "Baseline 2: Greedy (value-desc, cheapest feasible DC)")

    prob, a3 = solve(inst)
    print(f"\nILP solver status: {LpStatus[prob.status]}")
    m3 = report(inst, a3, "ILP baseline (PuLP/CBC, optimal)")

    print("\n=== Summary ===")
    print(f"{'Method':35s} {'Objective':>10s} {'Fill':>6s} {'Reassigned':>11s} {'Ship':>8s} {'Penalty':>8s}")
    for label, m in [("Default-assignment", m1), ("Greedy heuristic", m2), ("ILP (optimal)", m3)]:
        print(f"{label:35s} {m['objective']:10.2f} {m['fill_rate']:6.0%} {m['reassigned']:11d} {m['shipping']:8.2f} {m['penalty']:8.2f}")
