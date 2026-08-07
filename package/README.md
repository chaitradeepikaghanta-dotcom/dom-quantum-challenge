# DOM Solution — WISER × Nestlé Quantum Challenge

Team: Entangled minds

## What's in this folder

- `DOM_Solution_Pipeline.ipynb` — the full pipeline, already run once (you
  can see all real outputs without re-running anything).
- `real_data.py`, `baseline_pulp.py`, `qubo_qaoa.py`,
  `compare_quantum_algos.py`, `qaoa_small_subset.py` — the same code as
  standalone scripts, in case you want to run/edit pieces individually.
- `data_dictionary.md` — every file/field in the Nestlé data pack explained.
- `task3_formulation.md`, `task5_scaling_analysis.md` — write-ups for
  those tasks.
- `Technical_Report.docx` — the full 6-10 page report.
- `Planner_View.docx` — one-page business-language summary.

## Running

1. **Install Python 3.10+** if you don't have it.
2. **Install dependencies:**
   ```
   pip install pulp dimod dwave-samplers qiskit qiskit-aer pandas numpy scipy jupyter nbconvert
   ```
3. **Get the data pack:** copy your `DOM-data` folder (from the challenge
   Google Drive) into this same folder, so the structure looks like:
   ```
   your-project-folder/
   ├── DOM-data/
   │   ├── Example.xlsx
   │   ├── DOM Equations.docx
   │   ├── output_order_sku_level_data.csv
   │   ├── Output_order_level_data.csv
   │   └── input data/
   │       ├── input_order data.csv
   │       ├── input_shipping_cost_data.csv
   │       ├── input_dock_capacity.csv
   │       ├── input_throughput_capacity.csv
   │       └── input_capacity_planning.csv
   ├── DOM_Solution_Pipeline.ipynb
   ├── real_data.py
   ├── baseline_pulp.py
   ├── qubo_qaoa.py
   ├── compare_quantum_algos.py
   └── qaoa_small_subset.py
   ```
4. **Run the notebook:**
   ```
   jupyter notebook DOM_Solution_Pipeline.ipynb
   ```
   Then Kernel → Restart & Run All. You should see the same numbers
   already baked into the notebook (objective ≈447,822 for the ILP,
   99.2% for Steepest Descent, etc.) appear live on your machine.

## Expected runtime

- `real_data.py`, `baseline_pulp.py`: a few seconds
- `qubo_qaoa.py`: a few seconds
- `compare_quantum_algos.py`: ~2 minutes (Tabu Search is the slow part,
  ~100s by design — it's doing a much more thorough search)
- `qaoa_small_subset.py`: under a minute (includes brute-force + a real
  QAOA optimization loop)

## If something doesn't match

The results are seeded (`seed=7` throughout) so re-running should
reproduce the same numbers. If your pandas/qiskit versions differ
significantly, minor floating-point differences are normal; the overall
conclusions (ILP > Steepest Descent > Tabu > SA/PIQMC > Random) should
hold regardless.
