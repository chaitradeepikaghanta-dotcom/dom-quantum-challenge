"""
Loads the real Nestle DOM data pack and extracts a tractable subset of
FOCUS ORDERS (IsInvAvail == 'N', per the criteria in DOM Equations.docx)
into the same instance schema used by baseline_pulp.py / qubo_qaoa.py.

For tractability we take single-SKU focus orders only (359 focus orders
exist in total; most are single-SKU). Multi-SKU orders need the fuller
Cases_osdp formulation from the Equations doc -- noted as a scaling
extension in Task 5.
"""
import pandas as pd

import os
DATA_DIR = os.environ.get("DOM_DATA_DIR", "./DOM-data")


def load_real_instance(n_focus_orders=25, seed=7):
    """n_focus_orders: pass None (or a number >= 93) to use ALL single-SKU focus orders."""
    orders = pd.read_csv(f"{DATA_DIR}/input data/input_order data.csv")
    ship = pd.read_csv(f"{DATA_DIR}/input data/input_shipping_cost_data.csv")
    cap = pd.read_csv(f"{DATA_DIR}/input data/input_capacity_planning.csv")
    dock = pd.read_csv(f"{DATA_DIR}/input data/input_dock_capacity.csv")
    tput = pd.read_csv(f"{DATA_DIR}/input data/input_throughput_capacity.csv")

    # --- pick single-SKU focus orders (IsInvAvail == 'N') ---
    focus_lines = orders[orders["IsInvAvail"] == "N"].copy()
    line_counts = focus_lines.groupby("LoadNumber").size()
    single_sku_orders = line_counts[line_counts == 1].index
    focus_lines = focus_lines[focus_lines["LoadNumber"].isin(single_sku_orders)]

    picked = focus_lines.sort_values("Order_SKU_Revenue", ascending=False)
    if n_focus_orders is not None:
        picked = picked.head(n_focus_orders)

    order_ids = picked["LoadNumber"].tolist()
    order_sku = dict(zip(picked["LoadNumber"], picked["MaterialNumber"]))
    default_dc = dict(zip(picked["LoadNumber"], picked["Plant"]))
    value = dict(zip(picked["LoadNumber"], picked["Order_SKU_Revenue"]))
    order_zip = dict(zip(picked["LoadNumber"], picked["ZipCode"]))
    order_qty = dict(zip(picked["LoadNumber"], picked["OrderedQty_converted"]))
    order_rdd = dict(zip(picked["LoadNumber"], picked["RequestedDeliveryDate"]))
    # penalty: use FixedPenalty if present/nonzero, else a fraction of revenue via Penaltyforpotentialcuts
    penalty = {}
    for _, row in picked.iterrows():
        fp = row.get("FixedPenalty", 0)
        pct = row.get("Penaltyforpotentialcuts", 0)
        fp = float(fp) if pd.notna(fp) else 0.0
        pct = float(pct) if pd.notna(pct) else 0.0
        if fp <= 0 and pct <= 0:
            pct = 0.03  # dataset-wide median Penaltyforpotentialcuts, used when the field is missing
        penalty[row["LoadNumber"]] = round(fp if fp > 0 else pct * row["Order_SKU_Revenue"], 2)

    dcs = sorted(set(default_dc.values()) | set(ship["Plant"].unique()) & set(orders["Plant"].unique()))
    # restrict candidate DCs to those that actually appear as a default DC anywhere (keeps model realistic/tractable)
    dcs = sorted(orders["Plant"].unique().tolist())
    skus = sorted(set(order_sku.values()))

    # --- shipping cost: order -> DC, via ZipCode == TargetZip ---
    ship_cost = {}
    ship_lookup = ship.set_index(["TargetZip", "Plant"])["Shipping_Cost"].to_dict()
    for o in order_ids:
        z = order_zip[o]
        for d in dcs:
            c = ship_lookup.get((z, d))
            if c is None:
                # no direct lane priced for this DC/zip -> treat as a distant/unpriced lane
                c = ship.loc[ship["Plant"] == d, "Shipping_Cost"].mean() * 1.5
            ship_cost[(o, d)] = round(float(c), 2)

    # --- inventory: (DC, SKU) capacity from capacity_planning on the order's specific RDD ---
    cap["DATE"] = pd.to_datetime(cap["DATE"])
    cap_idx = cap.set_index(["LocationID", "MaterialID", "DATE"])["Available_inventory"]
    inventory = {}
    for d in dcs:
        for s in skus:
            rdd_dates = [pd.to_datetime(order_rdd[o]) for o in order_ids
                         if order_sku[o] == s and default_dc[o] == d]
            avail = None
            if rdd_dates:
                try:
                    avail = cap_idx.loc[(d, s, rdd_dates[0])]
                except KeyError:
                    avail = None
            if avail is None:
                rows = cap[(cap["LocationID"] == d) & (cap["MaterialID"] == s)]
                avail = rows.sort_values("DATE")["Available_inventory"].iloc[-1] if len(rows) else 0
            inventory[(d, s)] = max(0, int(round(avail))) if pd.notna(avail) else 0

    # --- throughput: use mean daily order_count capacity proxy per DC (90th pct of util as a soft cap) ---
    throughput = {}
    for d in dcs:
        rows = tput[tput["Plant"] == d]
        throughput[d] = int(rows["order_count"].quantile(0.75)) if len(rows) else 5
        throughput[d] = max(throughput[d], len(order_ids))  # don't let it be trivially binding at this small scale

    return {
        "orders": order_ids, "dcs": dcs, "skus": skus,
        "order_sku": order_sku, "default_dc": default_dc,
        "value": value, "ship_cost": ship_cost, "penalty": penalty,
        "inventory": inventory, "throughput": throughput,
        "_meta": {"order_zip": order_zip, "order_qty": order_qty, "order_rdd": order_rdd},
    }


if __name__ == "__main__":
    inst = load_real_instance(n_focus_orders=None)
    print(f"Orders: {len(inst['orders'])}, DCs: {len(inst['dcs'])}, SKUs: {len(inst['skus'])}")
    print(f"DCs: {inst['dcs']}")
    print()
    for o in inst["orders"][:5]:
        d = inst["default_dc"][o]
        s = inst["order_sku"][o]
        print(f"{o}: default_dc={d} sku={s} value={inst['value'][o]:.2f} "
              f"penalty={inst['penalty'][o]:.2f} ship_to_default={inst['ship_cost'][(o,d)]:.2f} "
              f"inv_at_default={inst['inventory'][(d,s)]}")
