# TRD: MemLab

## Stack
Python 3.11+, Streamlit, pandas, matplotlib (or plotly), pytest.

## Structure
```
memlab/
  app.py                # Streamlit UI (tabs: Allocation Lab, Worst-fit Scenario, Techniques, Benchmark)
  core/
    allocator.py        # Memory model + first/best/worst/next fit
    paging.py           # Paging and segmentation overhead calculators
    replacement.py      # FIFO, LRU, Optimal page replacement
    benchmark.py        # Random workload runner
    scenarios.py        # Preset scenarios (worst-fit scenario)
  tests/
  requirements.txt
  README.md
```

## Core model
- Memory is a list of blocks: `Block(start, size, owner)`; owner None means a hole.
- `allocate(size, strategy, pid)` returns the block or None; splits the chosen hole.
- `free(pid)` releases the block and merges adjacent holes.
- Strategy functions take the hole list and request size and return the chosen hole index:
  - first: first hole with size >= request
  - best: smallest hole with size >= request
  - worst: largest hole with size >= request
  - next: first fit starting from the last allocation position, wrapping around
- Every operation appends an event to a log so the UI can replay step by step.

## Metrics
- Utilization = allocated / total
- External fragmentation = 1 - largest_hole / total_free (0 if no free memory)
- Failure rate = failed / total requests
- Internal fragmentation (fixed partition, paging) = allocated block size - requested size
  (Segmentation has zero internal fragmentation but still suffers from external fragmentation)
- Page fault count, hit ratio = hits / references

## Worst-fit scenario (must be a unit test)
Holes [100, 120] KB, requests [60, 50, 50, 50] KB, no frees.
- Worst-fit: 60 -> 120 (60 left), 50 -> 100 (50 left), 50 -> 60 (10 left), 50 -> 50 (0 left). All succeed.
- Best-fit/First-fit/Next-fit: the last 50 KB request fails.
- Real-world reality: Worst-Fit is rarely preferred because it shreds large holes; real kernels use buddy and slab allocators.

## Page replacement checks (unit tests)
- Reference string 7,0,1,2,0,3,0,4,2,3,0,3,2,1,2,0,1,7,0,1 with 3 frames: FIFO 15, LRU 12, Optimal 9 faults.
- Belady string 1,2,3,4,1,2,5,1,2,3,4,5 with FIFO: 3 frames 9 faults, 4 frames 10 faults.

## UI
Minimal, light theme. Memory drawn as a horizontal bar (green allocated, grey holes). Four columns for the four strategies in the scenario tab.

## Testing
pytest for each strategy, merge-on-free, scenario, replacement algorithms. Run all tests before declaring done.

## Quality
Type hints, docstrings, no global state, deterministic seeds for benchmarks.