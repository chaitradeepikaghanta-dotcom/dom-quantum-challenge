# Task 3 — Mathematical Formulation

We formulate DOM as a **deterministic binary optimization model**, following
the structure Nestlé's own 2024 PoC used (`DOM Equations.docx`), simplified
to the single-SKU-per-order case implemented in `baseline_pulp_real.py` /
`qubo_qaoa_real.py`. The full multi-SKU version (Nestlé's original) is
given first for completeness, followed by the reduced version we actually
solve, with the simplification made explicit.

## 3.1 Nestlé's original formulation (multi-SKU, full model)

**Decision variables**
- `A_od ∈ {0,1}` — 1 if order `o` is fulfilled from DC `d`
- `Cases_osdp` — cases of SKU `s` for order `o` filled at DC `d`, PGI date `p`
- `Casepick_osdp`, `Palletpick_osdp` — case/pallet picks required for that fill
- `Penalty_Activation1_o`, `Penalty_Activation2_o ∈ {0,1}` — whether order `o` falls above/below its case-penalty threshold
- `Penalty_Cases1_os`, `Penalty_Cases2_os` — cases filled under each penalty regime

**Model parameters**
`Default_Inv_dsp`, `NonDefault_Inv_dsp` (inventory for default/diverted orders),
`Dock_Capacity_dp`, `Casepick_Capacity_dp`, `PalletPick_Capacity_dp`,
`Order_skuprice_os`, `Order_sku_demand_os`, `ShippingCost_od`,
`Order_perc_penalty_o`, `Order_level_threshold_o`, `Casesperpallet_s`.

**Objective:** `Max( Revenue − Penalty − Shipping Cost )`, where
- `Revenue = Σ Cases_osdp × Order_skuprice_os`
- `Penalty = Σ (Order_sku_demand_os × Penalty_Activation1_o − Penalty_Cases1_os) × Order_skuprice_os × Order_perc_penalty_o`
- `Shipping Cost = Σ ShippingCost_od × A_od`

**Constraints**
1. One DC per order: `Σ_d A_od ≤ 1`
2. Cases filled ≤ ordered qty, gated by assignment: `Cases_osdp ≤ A_od × Order_sku_demand_os`
3. Inventory: default + non-default cases filled at (d,s,p) ≤ available inventory, with non-default also bounded by the minimum inventory over the next 5 days (protects against short-term stockouts after a divert)
4. **Divert threshold:** a diverted order must improve fill rate at the alternate DC by **≥5%** over what the default DC could fill — `Casesfilled_od − Casesfillableatdefaultdc_o ≥ 1.05 × A_od × OrderedQty_o`
5. Case-pick/pallet-pick conversion: `Casespick_osdp + Palletpick_osdp × Casesperpallet_s = Cases_osdp`, aggregated to dock/case-pick/pallet-pick capacity per DC per day
6. Dock: total dock requests per (DC, date) ≤ `Dock_Capacity_dp` (one dock slot assumed per order)
7. Penalty activation logic: exactly one of `Penalty_Activation1_o`/`Penalty_Activation2_o` is active, and each bounds its own `Penalty_Cases` term against `Order_level_threshold_o`

## 3.2 Our reduced formulation (single-SKU orders, as implemented)

For the tractable subset (single-SKU focus orders — 93 of the 359 real
focus orders), `Cases_osdp` collapses to one case-quantity per (order, DC)
since each order has exactly one SKU and one relevant PGI date. This lets
us drop the SKU/date indices from the case-level variables while keeping
every constraint category above.

**Decision variable:** `x_{o,d} ∈ {0,1}` — order `o` assigned to DC `d`
(equivalent to Nestlé's `A_od`)

**Parameters** (all pulled from the real data pack, see `data_dictionary.md`):
- `value_o` = `Order_SKU_Revenue` (≈ `Order_skuprice_os × Order_sku_demand_os`, since one SKU per order)
- `ship_cost_{o,d}` = `Shipping_Cost` looked up by (customer ZIP, DC)
- `penalty_o` = `FixedPenalty` if set, else `Penaltyforpotentialcuts × value_o`
- `inv_{d,s}` = `Available_inventory` from the capacity-planning ledger, at the order's requested delivery date
- `throughput_d` = a capacity proxy from `input_throughput_capacity.csv`

**Objective (maximize):**
```
Σ_{o,d} (value_o − ship_cost_{o,d}) x_{o,d}  −  Σ_o penalty_o (1 − Σ_d x_{o,d})
```
This is Nestlé's `Revenue − Penalty − Shipping Cost`, with the penalty
applied whenever an order is left unassigned rather than through the
case-level threshold logic in constraint 7 (a simplification: we treat
each focus order as either fully divertable or fully penalized, rather
than modeling partial-cut penalty tiers).

**Constraints:**
- `Σ_d x_{o,d} ≤ 1` for all `o` — matches Nestlé's constraint 1 exactly
- `Σ_{o: sku(o)=s} x_{o,d} ≤ inv_{d,s}` for all `(d,s)` — matches constraint 3, collapsed to one date per order
- `Σ_o x_{o,d} ≤ throughput_d` for all `d` — a simplified stand-in for constraints 5/6 (case-pick/pallet-pick/dock), using order-count as a single capacity proxy rather than separately tracking case-picks, pallet-picks, and dock slots

**Dropped/simplified from the full model:** the ≥5% divert-improvement
threshold (constraint 4) and the two-tier penalty activation logic
(constraint 7) are not enforced explicitly — the objective's linear
penalty term serves as their stand-in. Re-adding constraint 4 exactly
would require also computing `Casesfillableatdefaultdc_o` (fill rate at
the *default* DC, not just whether it's fully sufficient), which the
current 0/1 `IsInvAvail` flag doesn't directly give us — a good target
for Task 5's scaling/refinement discussion.

## 3.3 How it's solved, and the accuracy/feasibility/runtime/scalability trade-off

- **Exact (ILP, PuLP/CBC):** solves the reduced model to provable
  optimality. At 93 orders × 8 DCs (744 binary variables) this takes
  under 2 seconds — the reduced model is small enough that exactness is
  free here. This won't hold once multi-SKU orders and the full
  constraint set (dock/case-pick/pallet-pick separately, the 5%
  threshold) are reintroduced — see Task 5.
- **Quantum-inspired (QUBO + simulated annealing):** the same objective
  and constraints are re-encoded as an unconstrained QUBO (constraints
  become penalty terms — see `qubo_qaoa_real.py` for the one-sided
  penalty design used to avoid penalizing valid low-utilization
  assignments). This scales the same way a QAOA circuit would (one qubit
  per order-DC pair), but is solved here by classical simulated annealing
  since 744 qubits is far beyond real statevector-simulator or current
  QPU limits — a genuine QAOA run would need a much smaller batch. The
  trade-off: annealing reaches 71% fill / objective 369,752 vs. the ILP's
  53% fill / objective 447,822 (interestingly, ILP prioritizes value over
  raw fill rate — see the baseline comparison in Task 2/4) — a
  reasonable but visibly sub-optimal result, illustrating the
  accuracy-vs-scalability trade-off directly.
