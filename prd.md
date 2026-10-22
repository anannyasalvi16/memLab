# PRD: MemLab — Memory Management Performance Lab

## 1. Overview
MemLab is a Python + Streamlit app that simulates how an operating system manages main memory and lets a user compare the performance of each technique side by side. It answers two Module 4 questions:
1. Discuss the performance of all memory management techniques.
2. Design a scenario showing that worst-fit may be a good algorithm for dynamic partitioning.

## 2. Goals
- Make memory management performance visible with live charts, not just theory.
- Prove, with a runnable scenario, that worst-fit can beat first-fit, best-fit and next-fit.
- Be simple, minimal, and demo-able in under 5 minutes.

## 3. Users
Students and faculty reviewing OS Module 4; anyone learning memory management.

## 4. Features
### F1. Contiguous allocation lab (dynamic partitioning)
- Memory bar showing allocated blocks and holes.
- Strategies: First-fit, Best-fit, Worst-fit, Next-fit.
- Inputs: total memory, list of holes (or empty memory), list of requests (alloc/free).
- Output metrics per strategy: requests satisfied, requests failed, memory utilization, external fragmentation, largest free hole, number of holes.

### F2. Worst-fit scenario (Question 2)
- Preset scenario: holes of 100 KB and 120 KB; requests 60, 50, 50, 50 KB.
- Step-by-step replay for all four strategies side by side.
- Expected result: worst-fit satisfies all 4 requests; first-fit, best-fit and next-fit fail the last request.
- Explanation panel: why worst-fit leaves a usable remainder while best-fit leaves a sliver.
- Honesty panel: a random-workload run showing worst-fit does not always win.

### F3. Technique comparison (Question 1)
- Fixed partitioning: internal fragmentation.
- Dynamic partitioning: external fragmentation, compaction.
- Paging: internal fragmentation (last page), page table overhead.
- Segmentation: external fragmentation, segment table overhead.
- Virtual memory page replacement: FIFO, LRU, Optimal; page fault counts and hit ratio; Belady's anomaly demo.
- A summary table that scores every technique on fragmentation, speed, overhead and flexibility.

### F4. Random workload benchmark
- Run N random workloads per strategy; show average failure rate and fragmentation as bar charts.

## 5. Non-goals
No real OS memory manipulation; simulation only. No user accounts.

## 6. Success criteria
- Worst-fit scenario reproduces exactly as specified.
- All algorithms pass unit tests.
- App runs with `streamlit run app.py` and demos cleanly.

## 7. Deliverables
Working app, README, PPT, short demo script.