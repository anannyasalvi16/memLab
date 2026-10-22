# MemLab: Memory Management Performance Lab

> **A runnable, interactive OS memory management simulator built with Python and Streamlit.**  
> Designed to explore Module 4 Operating Systems concepts and answer core theoretical and empirical questions.

---

## 📌 Overview

MemLab answers two fundamental Operating Systems questions through live simulations and quantitative benchmarks:
1. **Discuss the performance of all memory management techniques.**  
   *Evaluates Fixed Partitioning, Dynamic Partitioning, Simple Paging, Segmentation, Paged Segmentation, and Virtual Memory Page Replacement (FIFO, LRU, Optimal) alongside Belady's Anomaly.*
2. **Design a scenario showing that Worst-Fit may be a good algorithm for dynamic partitioning.**  
   *Provides a deterministic 4-request scenario where Worst-Fit satisfies 100% of allocations while First-Fit, Best-Fit, and Next-Fit all fail the final allocation due to external fragmentation.*

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.11+ (Tested on Python 3.14.6)
- Dependencies: `streamlit`, `pandas`, `plotly`, `pytest`

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

### 4. Run Unit Tests
```bash
pytest
```
All 13 unit tests execute in under 0.1 seconds.

---

## 🏗️ Architecture & Project Structure

```
OS/
├── app.py                      # Streamlit UI dashboard with 4 tabs
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── README.md                   # Project documentation & OS theory
├── demo_script.md              # 5-minute presentation & viva walkthrough
├── presentation.md             # Complete slide deck outline for Module 4
├── core/
│   ├── __init__.py
│   ├── models.py               # Block, AllocationEvent, AllocationMetrics dataclasses
│   ├── allocator.py            # Dynamic partitioning allocator (First/Best/Worst/Next-Fit)
│   ├── scenarios.py            # Preset Worst-Fit superiority scenario
│   ├── paging.py               # Paging & segmentation overhead and fragmentation calculators
│   ├── replacement.py          # Page replacement simulators (FIFO, LRU, Optimal, Belady)
│   └── benchmark.py            # Monte Carlo random workload generator & benchmark runner
├── components/
│   ├── __init__.py
│   ├── visualizer.py           # Plotly & HTML/CSS stacked horizontal memory bars
│   └── metrics.py              # Metric cards and styling utilities
└── tests/
    ├── __init__.py
    ├── test_allocator.py       # Allocator unit tests (fits, coalescing, wraparound)
    ├── test_scenarios.py       # Worst-fit scenario reproduction tests
    ├── test_replacement.py     # Page replacement & Belady's anomaly tests
    └── test_paging.py          # Fragmentation and overhead tests
```

---

## 🔍 The Four Labs

### Tab 1: Dynamic Partitioning Allocation Lab
- **Strategies Supported:** First-Fit, Best-Fit, Worst-Fit, Next-Fit.
- **Interactive Operations:** Allocate processes with custom sizes, free active blocks with automatic bidirectional hole merging.
- **Event Replay Slider:** Step back and forth through every memory operation to inspect the exact memory layout at that point in time.
- **Live Metrics:** Memory utilization, external fragmentation index, largest hole size, and failure rate.

### Tab 2: Worst-Fit Superiority Scenario (Question 2)
- **Initial Setup:** Holes of **100 KB** and **120 KB** (separated by an immovable 20 KB reserved OS block). Total free memory: **220 KB**.
- **Request Sequence:** **60 KB (P1)** &rarr; **50 KB (P2)** &rarr; **50 KB (P3)** &rarr; **50 KB (P4)**. Total requested: **210 KB**.
- **Mathematical Trace:**
  - **Worst-Fit:**
    1. `60 KB` &rarr; placed in `120 KB` hole &rarr; leaves a **60 KB remainder** (Holes: `[100, 60]`).
    2. `50 KB` &rarr; placed in `100 KB` hole &rarr; leaves a **50 KB remainder** (Holes: `[50, 60]`).
    3. `50 KB` &rarr; placed in `60 KB` hole &rarr; leaves a **10 KB remainder** (Holes: `[50, 10]`).
    4. `50 KB` &rarr; placed in `50 KB` hole &rarr; exact fit! **All 4 requests succeed (100% satisfied)**.
  - **First-Fit, Best-Fit & Next-Fit:**
    1. `60 KB` &rarr; placed in `100 KB` hole &rarr; leaves an unusable **40 KB sliver** (Holes: `[40, 120]`).
    2. `50 KB` &rarr; placed in `120 KB` hole &rarr; leaves a `70 KB` hole (Holes: `[40, 70]`).
    3. `50 KB` &rarr; placed in `70 KB` hole &rarr; leaves an unusable **20 KB sliver** (Holes: `[40, 20]`).
    4. `50 KB` &rarr; **FAILS!** (Total free memory is 60 KB, but largest hole is only 40 KB. Allocation fails due to external fragmentation).
- **Side-by-Side Visualization:** 4 simultaneous columns with HTML memory bars and a decision matrix.
- **Honesty Panel:** Explains why Worst-Fit is not universally optimal for real-world operating systems.

### Tab 3: Techniques Comparison & Page Replacement (Question 1)
- **Comprehensive Matrix:** Compares Fixed Partitioning, Dynamic Partitioning, Paging, Segmentation, and Paged Segmentation.
- **Interactive Calculators:**
  - Paging Overhead Calculator (pages required, internal fragmentation on last page, page table bytes).
  - Fixed Partitioning Calculator (internal fragmentation per partition, rejected requests).
- **Page Replacement Simulator:**
  - Simulates FIFO, LRU, and Optimal algorithms.
  - Step-by-step frame matrix tracking hit/fault per reference.
  - Verified against textbook reference string: `7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1` with 3 frames (FIFO: 15, LRU: 12, Optimal: 9 faults).
- **Belady's Anomaly Live Demo:**
  - Interactive plot of faults vs. frames for reference string `1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5`.
  - Empirically proves that increasing frames from 3 to 4 increases FIFO faults from 9 to 10.

### Tab 4: Benchmark & Honesty
- **Monte Carlo Simulator:** Runs $N$ randomized workloads with configurable operations, memory size, and deterministic seeds.
- **Empirical Visualizations:** Grouped Plotly bar charts comparing Average Failure Rate, External Fragmentation, and Utilization across all four strategies.
- **Counterexample Proof:** Demonstrates that Worst-Fit loses under heterogeneous workloads because it rapidly breaks down large contiguous holes into medium fragments.

---

## 🧪 Verification & Testing

Run all unit tests:
```bash
pytest -v
```

All 13 tests cover:
- Dynamic allocator first-fit, best-fit, worst-fit, next-fit logic.
- Adjacent hole coalescing upon block deallocation.
- Next-fit circular wraparound.
- Exact Worst-Fit scenario outcome (Worst-Fit: 4/4; others: 3/4).
- Page replacement fault counts for standard reference string.
- FIFO Belady's anomaly (3 frames = 9 faults, 4 frames = 10 faults).
- Overhead and fragmentation mathematics.
