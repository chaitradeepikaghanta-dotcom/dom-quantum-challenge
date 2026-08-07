# 📦 Quantum Optimization for Distributed Order Management

### WISER × Nestlé Global Quantum+AI Program 2026

**Team: Entangled Minds**

## 🎯 The Problem

Nestlé operates multiple distribution centers that fulfill customer orders. When an order's default distribution center cannot fulfill it due to inventory or operational constraints, the order may need to be reassigned to an alternative distribution center.

The challenge is to determine **which orders should be reassigned, where they should be fulfilled from, and whether the additional fulfillment cost is justified**—while respecting distribution-center capacity constraints.

We formulate this as a binary optimization problem and benchmark classical, quantum-inspired, and quantum approaches using real 2024 Nestlé proof-of-concept data.

---

## 🚀 What We Built

Rather than evaluating a single optimization technique, we benchmarked multiple approaches on the same real-world problem:

* **Default Assignment Baseline** — evaluates the existing allocation without reassignment.
* **Greedy Heuristic** — prioritizes feasible reassignment decisions sequentially.
* **Exact ILP Solver** — provides the optimization benchmark and provably optimal solution for the reduced instance.
* **Five Quantum-Inspired Algorithms** — Simulated Annealing, Tabu Search, Steepest Descent, Path-Integral Quantum Monte Carlo, and Random Sampling.
* **QAOA** — an actual gate-based Quantum Approximate Optimization Algorithm circuit implemented and evaluated on a small real-data subset.

### Key Result

The exact ILP solver recovered **$447,822 in order value**, compared with **$229,995 for the default-assignment baseline**.

Remarkably, **Steepest Descent achieved 99.2% of the ILP objective in only 0.08 seconds**, outperforming the other quantum-inspired approaches on the tested instance.

Our QAOA implementation successfully demonstrated the quantum approach on a small subset, but showed a **25.1% optimality gap**. This highlights the current scale limitations of quantum hardware and simulation rather than claiming an artificial quantum advantage.

---

## 📊 Results

| Method               | Objective Value ($) |            Fill Rate |
| -------------------- | ------------------: | -------------------: |
| Default Assignment   |             229,995 |                  14% |
| Greedy               |             412,060 |                  89% |
| **Exact ILP**        |         **447,822** |              **53%** |
| **Steepest Descent** |         **444,071** |              **53%** |
| QAOA (6 qubits)      |                   — | 25.1% optimality gap |

**Important:** Fill rate alone does not represent the optimization objective. Our evaluation considers the value recovered and the associated fulfillment costs and constraints.

For the complete methodology, formulation, experiments, and analysis, see:

`package/Technical_Report.docx`

---

## 🔬 Why This Project Stands Out

### 1. Real Industrial Data

The experiments use Nestlé's 2024 proof-of-concept data rather than synthetic benchmark data.

### 2. Fair Algorithmic Comparison

Five quantum-inspired approaches were evaluated on the same optimization instance, allowing direct comparison of solution quality and runtime.

### 3. Actual QAOA Implementation

We implemented and executed a gate-based QAOA circuit rather than stopping at a theoretical QUBO formulation.

### 4. Honest Benchmarking

Our results do not assume that quantum approaches automatically outperform classical methods. The experiments show where current methods perform well—and where they do not.

### 5. Reproducible Pipeline

The repository contains the executed notebook, standalone scripts, mathematical formulation, technical documentation, and setup instructions.

---

## 📁 Repository Structure

```text
package/
│
├── DOM_Solution_Pipeline.ipynb
│   └── Complete end-to-end analysis pipeline
│
├── real_data.py
│   └── Real-data loading and preprocessing
│
├── baseline_pulp.py
│   └── Baselines and exact ILP optimization
│
├── qubo_qaoa.py
│   └── QUBO formulation and quantum encoding
│
├── compare_quantum_algos.py
│   └── Quantum-inspired algorithm benchmarking
│
├── qaoa_small_subset.py
│   └── Gate-based QAOA implementation
│
├── data_dictionary.md
│   └── Dataset column definitions
│
├── task3_formulation.md
│   └── Mathematical formulation
│
├── task5_scaling_analysis.md
│   └── Scaling limitations and future improvements
│
├── Technical_Report.docx
├── Task1_Business_Technical_Summary.docx
└── Planner_View.docx
```

---

## ⚙️ Installation

Install the required Python packages:

```bash
pip install pulp dimod dwave-samplers qiskit qiskit-aer pandas numpy scipy jupyter
```

### Running the Project

1. Obtain the authorized `DOM-data` folder from the WISER workspace.
2. Place the data folder inside `package/`.
3. Open:

```text
DOM_Solution_Pipeline.ipynb
```

4. Select **Restart & Run All** in Jupyter Notebook.

### 🔐 Data & Privacy

The original Nestlé data pack is **not included in this public repository**.

The dataset is excluded using `.gitignore` in accordance with the applicable WISER/Nestlé data-handling requirements.

Only permitted aggregate results and anonymized identifiers are included in the public repository.

**No confidential or proprietary data is intentionally included in this repository.**

---

## 📈 Future Work

The project can be extended through:

* Scaling the optimization using distribution-center clustering.
* Supporting multi-SKU orders using the complete formulation.
* Reintroducing the full Nestlé constraint and penalty structure.
* Systematic QUBO penalty-weight optimization.
* Order-level validation against authorized Nestlé PoC recommendations.
* Deployment as a planner-facing optimization and decision-support system.
* Evaluation on larger quantum hardware as quantum systems scale.

---

## 📚 Documentation

* **Technical Report:** `package/Technical_Report.docx`
* **Business & Technical Summary:** `package/Task1_Business_Technical_Summary.docx`
* **Planner View:** `package/Planner_View.docx`
* **Mathematical Formulation:** `package/task3_formulation.md`
* **Scaling Analysis:** `package/task5_scaling_analysis.md`
* **Data Dictionary:** `package/data_dictionary.md`

---

## 👥 Team

**Team: Entangled Minds**

| Member        | Role / Contribution | Email |
| ------------- | ------------------- | ----- |
| Team Member 1 | —                   | —     |
| Team Member 2 | —                   | —     |
| Team Member 3 | —                   | —     |
| Team Member 4 | —                   | —     |

---

## 🙏 Acknowledgements

This project was developed as part of the **WISER × Nestlé Global Quantum+AI Program 2026**.

We acknowledge the program-provided data, documentation, and resources used for this project.

External libraries and tools used include **Python, NumPy, Pandas, SciPy, PuLP, D-Wave Samplers, Qiskit, and Qiskit Aer**.

---

## 📌 Submission

**Program:** WISER × Nestlé Global Quantum+AI Program 2026
**Team:** Entangled Minds
**Project:** Quantum Optimization for Distributed Order Management
**Submission Date:** August 7, 2026

```
```
