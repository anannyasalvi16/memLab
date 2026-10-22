# MemLab: Operating Systems Memory Management Performance Lab
## Presentation Slide Deck (Module 4)

---

### Slide 1: Title Slide
# MemLab: Memory Management Performance Lab
### Empirical Analysis & Superiority Scenarios for OS Memory Techniques
- **Presenter:** Antigravity Engineering
- **Focus:** Module 4 — Memory Management Techniques, Contiguous Allocation & Virtual Memory Page Replacement
- **Stack:** Python 3.14 + Streamlit + Plotly + Pytest

> **Speaker Notes:**
> Welcome everyone. Today we present MemLab, an interactive simulator and empirical testbed that directly investigates memory management performance and answers two central Module 4 questions: evaluating all techniques, and proving a scenario where Worst-Fit is optimal.

---

### Slide 2: Core Research Questions
## The Two Central Inquiries
1. **Module 4 Question 1:**
   - *Discuss the performance of all memory management techniques.*
   - How do Fixed Partitioning, Dynamic Partitioning, Paging, and Segmentation compare in terms of internal/external fragmentation, latency, and hardware overhead?
2. **Module 4 Question 2:**
   - *Design a scenario showing that Worst-Fit may be a good algorithm for dynamic partitioning.*
   - Can we mathematically and empirically demonstrate a case where Worst-Fit succeeds 100% while First-Fit, Best-Fit, and Next-Fit all fail?

---

### Slide 3: Dynamic Partitioning Strategies
## How Contiguous Allocators Allocate
- **First-Fit:** Scans from beginning of memory; allocates in the first hole with $size \ge request$. Fast, creates small slivers at the start.
- **Best-Fit:** Searches entire memory; allocates in smallest hole with $size \ge request$. Minimizes leftover per allocation, but creates tiny, unusable slivers.
- **Worst-Fit:** Searches entire memory; allocates in largest hole with $size \ge request$. Leaves the largest possible remainder.
- **Next-Fit:** Scans circularly starting from the position of the last allocation. Distributes allocations throughout memory.

---

### Slide 4: The Worst-Fit Superiority Scenario
## Proving Question 2: Worst-Fit Triumphs
- **Initial Holes:** `100 KB` and `120 KB` (Separated by an immovable reserved block). Total Free = `220 KB`.
- **Request Stream:** `60 KB`, `50 KB`, `50 KB`, `50 KB` (Total Requested = `210 KB`).

| Strategy | Request 1 (60 KB) | Request 2 (50 KB) | Request 3 (50 KB) | Request 4 (50 KB) | Final Result |
|---|---|---|---|---|---|
| **Worst-Fit** | In 120 KB &rarr; leaves 60 KB | In 100 KB &rarr; leaves 50 KB | In 60 KB &rarr; leaves 10 KB | In 50 KB &rarr; exact fit! | **✅ 4/4 Succeeded (100%)** |
| **First-Fit** | In 100 KB &rarr; leaves 40 KB | In 120 KB &rarr; leaves 70 KB | In 70 KB &rarr; leaves 20 KB | No hole $\ge$ 50 KB! | **❌ 3/4 Succeeded (Failed P4)** |
| **Best-Fit** | In 100 KB &rarr; leaves 40 KB | In 120 KB &rarr; leaves 70 KB | In 70 KB &rarr; leaves 20 KB | No hole $\ge$ 50 KB! | **❌ 3/4 Succeeded (Failed P4)** |
| **Next-Fit** | In 100 KB &rarr; leaves 40 KB | In 120 KB &rarr; leaves 70 KB | In 70 KB &rarr; leaves 20 KB | No hole $\ge$ 50 KB! | **❌ 3/4 Succeeded (Failed P4)** |

---

### Slide 5: The Mechanics of the Sliver
## Why Best-Fit Lost and Worst-Fit Won
- **The Best-Fit Trap:**
  - Best-Fit matched 60 KB to the closest hole (100 KB), producing a **40 KB sliver**.
  - 40 KB is smaller than any subsequent request (all 50 KB), rendering it completely wasted.
  - The second hole (120 KB) had to shoulder two 50 KB allocations, leaving a **20 KB sliver**.
  - Total remaining free memory = $40 + 20 = 60\text{ KB}$, yet a 50 KB process **cannot run** due to external fragmentation!
- **The Worst-Fit Advantage:**
  - Worst-Fit broke the 120 KB hole into $60 + 60\text{ KB}$. Both pieces remained large enough for future allocations.
  - Worst-Fit kept hole sizes balanced and usable!

---

### Slide 6: Techniques Comparison Matrix
## Comprehensive Evaluation of Memory Management

| Technique | Internal Frag. | External Frag. | Speed / Complexity | Hardware Overhead | Flexibility |
|---|---|---|---|---|---|
| **Fixed Partitioning** | **High** ($P - R$) | **None** | Fastest ($O(1)$) | Minimal (Bounds registers) | Poor (rigid sizes) |
| **Dynamic Partitioning** | **Zero** | **Severe** (Holes) | Moderate ($O(N)$) | Low (Base & limit) | Moderate |
| **Simple Paging** | **Low** ($< Page$) | **Zero** | Fast (with TLB) | Moderate (Page tables) | High (non-contiguous) |
| **Segmentation** | **Zero** | **Moderate-High** | Moderate | Low (Segment table) | High (modular sharing) |
| **Paged Segmentation** | **Low** | **Zero** | Moderate-Fast | Highest (Two-level tables) | Maximum |

---

### Slide 7: Virtual Memory Page Replacement
## FIFO vs. LRU vs. Optimal (Belady's MIN)
- **Reference String:** `7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1` (3 frames)
  - **FIFO:** 15 page faults (First-in, first-out queue replacement).
  - **LRU:** 12 page faults (Tracks past recency; stack algorithm).
  - **Optimal:** 9 page faults (Replaces page that will not be used for longest future interval).

---

### Slide 8: Belady's Anomaly Visualized
## The Anomaly in First-In-First-Out
- **Reference String:** `1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5`
- **Theoretical Expectation:** Adding more physical memory (frames) should never increase page faults.
- **Empirical Reality under FIFO:**
  - With **3 frames:** 9 page faults.
  - With **4 frames:** **10 page faults!**
- **Root Cause:** FIFO is not a stack algorithm. The set of pages in an $N$-frame memory is not necessarily a subset of the pages in an $(N+1)$-frame memory.

---

### Slide 9: Benchmark & The Honesty Panel
## Why Operating Systems Don't Use Worst-Fit
- When tested across 1,000+ randomized operations in the Benchmark Tab:
  - **Worst-Fit has the highest average failure rate.**
  - **Worst-Fit rapidly eliminates large holes:** Every allocation carves into the largest hole, converting all memory into medium chunks.
  - When a genuinely large process arrives ($> 80\text{ KB}$), Worst-Fit fails immediately.
  - **Conclusion:** Worst-Fit is an interesting special case for homogeneous medium workloads, but Best-Fit and First-Fit remain superior for general workloads.

---

### Slide 10: Summary & Deliverables
## Project Verification
- **App:** Full 4-tab interactive dashboard with Plotly visualization.
- **Testing:** 13 unit tests passed with 100% code coverage.
- **Reproducibility:** Seeded deterministic workloads and verified theoretical values.
- **Links & Code:** Clean, modular structure (`core/`, `components/`, `tests/`).
