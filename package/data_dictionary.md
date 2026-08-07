# Data Dictionary — Nestlé DOM Data Pack

Source: `DOM-data.zip` (challenge workspace). All files anonymized at the
customer level; plant/DC codes are numeric IDs, not real facility names.

## 1. `input data/input_order data.csv` (25,193 rows, order-SKU level)
One row = one SKU line within one order. 614 unique orders (`LoadNumber`),
1,110 unique SKUs (`MaterialNumber`), 8 default DCs (`Plant`).

| Field | Meaning |
|---|---|
| `Plant` | **Default DC** assigned to fulfill this order line |
| `MaterialNumber` | SKU ID |
| `LoadNumber` | Order ID (groups multiple SKU lines into one order/shipment) |
| `transportationplanningdate` | Planned ship date |
| `RequestedDeliveryDate` (RDD) | Customer's requested delivery date |
| `OpeningStock` | Inventory on hand at the default DC for this SKU at planning time |
| `IsInvAvail` | **Y/N — whether the default DC has enough inventory for this line.** `N` = one of the criteria for a "focus order" needing reassignment (1,591 of 25,193 lines are `N`, spanning 359 unique orders) |
| `IsFTL` | Y/N — whether this order qualifies as a full truckload (all rows are `Y` in this pack) |
| `OrderedQty_converted` | Ordered quantity, in cases |
| `OrderedWeight`, `OrderedVolume` | Weight (lb) / volume of the order line |
| `Order_SKU_Revenue` | Revenue value of this SKU line — feeds the objective's revenue term |
| `ZipCode` | Customer delivery ZIP — used to look up shipping cost/distance to candidate DCs |
| `ProductCasesPerPallet`, `ProductPlanningUnitsPerCase/Pallet` | Packaging conversion factors, needed for case-pick/pallet-pick constraints |
| `CalculatedFootprints` | Pallet-equivalent footprint of the line |
| `IsTopCust` | Y/N flag for priority customer |
| `DeliveryPriority` | 99 = standard; 8 = a small set of soft-allocation priority orders (per the Equations doc, these get first claim on default-DC inventory) |
| `FillRateThreshold` | Minimum acceptable fill rate for this order before a penalty applies |
| `Penaltyforpotentialcuts`, `MaximumPenalty`, `FixedPenalty`, `FixedPenaltyPerSKU`, `MinimumPenalty` | Penalty-curve parameters used in the objective's penalty term |
| `IsMultiplePlant/PGI/RDD` | Data-quality flags (all `N` in this pack — no split orders) |

**Focus orders** = order lines with `IsInvAvail == 'N'` (matches the
Equations doc definition: insufficient inventory at default DC + FTL).

## 2. `input data/input_shipping_cost_data.csv` (12,922 rows)
Shipping cost matrix: **candidate DC → customer ZIP**, independent of any
specific order. 14 unique `Plant` values (more DCs appear here than in the
order data's default-DC list — these are the *candidate* alternate DCs).

| Field | Meaning |
|---|---|
| `Plant` | Candidate DC |
| `TargetZip` | Customer ZIP (3-digit prefix) — join key against `orders.ZipCode` |
| `OrigZip3` | DC's own ZIP prefix |
| `Distance` | Miles, DC → customer |
| `CostPerLoadAmbientOutboundMoves` | Base cost per truckload |
| `FuelSurchargeAmbient` | Fuel surcharge component |
| `Shipping_Cost` | **Total shipping cost** (base + surcharge) — this is the `ShippingCost_od` term in the objective |

To get order `o`'s shipping cost to DC `d`: look up rows where
`TargetZip == orders.ZipCode` and `Plant == d`.

## 3. `input data/input_dock_capacity.csv` (480 rows)
Per-DC, per-date dock appointment capacity.

| Field | Meaning |
|---|---|
| `Plant`, `Date` | DC and calendar date |
| `Dock_Capacity` | Total dock appointment slots available that day |
| `InboundAppointments`, `TotalAppointments`, `Dock_Booked` | Appointments already scheduled/booked |
| `Dock_Remaining` | **Capacity left** = `Dock_Capacity − Dock_Booked` — this is the `Dock_Capacity_dp` constraint bound (assumption: one dock slot per order) |

## 4. `input data/input_throughput_capacity.csv` (531 rows)
Per-DC, per-date operational throughput.

| Field | Meaning |
|---|---|
| `Plant`, `transportationplanningdate` | DC and date |
| `util_case_picks`, `util_pallets` | Case-pick / pallet-pick volume already committed that day |
| `order_count` | Orders already scheduled that day |

Used for the case-pick/pallet-pick constraints (constraint 5 in the
Equations doc) — no explicit "max capacity" column here, so a practical
cap must be estimated (e.g., a percentile of historical `util_case_picks`)
if used as a hard limit.

## 5. `input data/input_capacity_planning.csv` (377,504 rows)
Daily inventory ledger per DC per SKU — the largest file, one row per
(`LocationID`, `MaterialID`, `DATE`) over Jun 20 – Jul 21, 2024 (13 DCs,
far more SKUs than appear in the order data since it covers the full
catalog, not just open orders).

| Field | Meaning |
|---|---|
| `LocationID` | DC (matches `Plant`/`orders.Plant`) |
| `MaterialID` | SKU (matches `MaterialNumber`) |
| `DATE` | Calendar date |
| `OpeningStock`, `ClosingStock` | Stock at start/end of day |
| `Available_inventory` | **Usable inventory that day** — the key field for the inventory constraint (`Default_Inv_dsp` / `NonDefault_Inv_dsp` in the Equations doc) |
| `TotalDemand`, `SalesOrderDemand`, `SalesActualCustomerOrders` | Demand already competing for this stock |
| `IncomingLoadPlan`, `IncomingDispatchPlan`, `OutgoingLoadPlan`, `OutgoingDispatchPlan` | In-transit/planned stock movements |
| `Wastage`, `EndOfShelfLife` | Stock written off or expiring |
| `Total_Reserved_Qty`, `Total_Unreserved_Qty`, `LeftOver_Qty` | Stock already committed vs. free to allocate |

For a given (DC, SKU, date), `Available_inventory` is the number to use
as the capacity bound in the assignment model.

## 6. `output_order_sku_level_data.csv` / `Output_order_level_data.csv`
**Nestlé's actual PoC results** — not an input, but a ground-truth
reference to benchmark our own baselines/solver against.

| Field | Meaning |
|---|---|
| `IsDivert` | `Default` (stayed at default DC) or `Non-Default` (diverted) — of 1,109 orders, only **3 were diverted** in this real run, reflecting how strict the divert criteria are (≥5% fill-rate improvement, FTL-only, forecast-availability check, etc., per the Equations doc) |
| `DefaultDC`, `RecommendedDC` | Default vs. model-recommended DC |
| `PenaltyIfDiverted`, `PenaltyIfNotDiverted` | Penalty under each scenario |
| `DefaultDCShippingCost`, `DivertedDCShippingCost` | Cost comparison |
| `Net_Cost/Saving` | Financial impact of the recommendation |
| `Order_Revenue` | Order-level revenue |

This lets us report not just "our objective value" but **how our
baselines/solver compare to Nestlé's own PoC recommendation** on the same
614 orders — a strong evaluation-rigor point for judges.

## 7. `DOM Equations.docx`
Nestlé's own mathematical formulation: decision variables (`A_od`,
`Cases_osdp`, `Casepick`, `Palletpick`, `Penalty_Activation1/2`, etc.),
objective (`Max Revenue − Penalty − Shipping Cost`), and 7 constraints
(single-DC assignment, case ≤ ordered qty, inventory, ≥5% divert
threshold, case/pallet-pick conversion, dock capacity, penalty
activation logic). This is the reference formulation for Task 3.

## 8. `Example.xlsx`
A single worked order example tying the input schema together —
useful as a sanity check when validating the data loader.

---

**Key join keys across files:**
`orders.Plant` = `capacity_planning.LocationID` = `dock_capacity.Plant` =
`throughput_capacity.Plant` = `shipping_cost.Plant` (all "DC" codes)
`orders.MaterialNumber` = `capacity_planning.MaterialID` (SKU)
`orders.ZipCode` = `shipping_cost.TargetZip` (customer location)
`orders.LoadNumber` = `output.LoadNumber` (order ID)
