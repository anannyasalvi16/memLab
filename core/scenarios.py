from __future__ import annotations
from typing import Dict, List, Tuple
from core.models import Block, AllocationEvent
from core.allocator import MemoryAllocator


def get_worst_fit_preset_blocks() -> List[Block]:
    """
    Constructs the initial memory blocks with holes of 100 KB and 120 KB,
    separated by an immovable 20 KB reserved OS block.
    """
    return [
        Block(start=0, size=100, owner=None),            # Hole 1: 100 KB
        Block(start=100, size=20, owner="OS_RESERVED"),  # Reserved block
        Block(start=120, size=120, owner=None),          # Hole 2: 120 KB
    ]


PRESET_REQUESTS: List[Tuple[str, int]] = [
    ("P1", 60),
    ("P2", 50),
    ("P3", 50),
    ("P4", 50),
]


def run_worst_fit_scenario(strategy: str) -> MemoryAllocator:
    """
    Executes the preset scenario for a given strategy.
    Returns the populated MemoryAllocator with full event history.
    """
    initial_blocks = get_worst_fit_preset_blocks()
    allocator = MemoryAllocator.from_blocks(initial_blocks, strategy=strategy)

    for pid, size in PRESET_REQUESTS:
        allocator.allocate(size=size, pid=pid)

    return allocator


def run_all_strategies_for_preset() -> Dict[str, MemoryAllocator]:
    """
    Runs the preset scenario across all four allocation strategies.
    Returns a mapping: strategy_key -> MemoryAllocator
    """
    strategies = ["first_fit", "best_fit", "worst_fit", "next_fit"]
    return {strat: run_worst_fit_scenario(strat) for strat in strategies}


SCENARIO_EXPLANATION = """
### Why Worst-Fit Wins Here:
- **Worst-Fit** always chooses the largest available hole (120 KB), carving out 60 KB and leaving a **large, usable 60 KB remainder**.
- Next, the two 50 KB requests are placed into the 100 KB hole (leaving 50 KB) and the 60 KB remainder (leaving 10 KB).
- When the final 50 KB request arrives, the 50 KB remainder is **an exact fit**, allowing all four allocations to succeed!

### Why First, Best, and Next-Fit Fail:
- **Best-Fit** and **First-Fit** both pick the 100 KB hole for the 60 KB request because 100 KB is the closest fit (or first).
- This leaves a small, unusable **40 KB sliver**.
- Subsequent allocations consume the 120 KB hole in two chunks (50 KB and 50 KB), leaving another **20 KB sliver**.
- When the final 50 KB request arrives, total free memory is 60 KB (40 KB + 20 KB), but it is split into two non-contiguous slivers.
- Thus, the 4th request **fails due to external fragmentation**!
"""

HONESTY_NOTE = """
> **Honesty & Practical Realities Note**:
> While Worst-Fit triumphs in this carefully structured scenario, Worst-Fit is rarely preferred because it shreds large holes; real kernels use buddy and slab allocators. In general workloads, it systematically breaks down largest holes into medium ones, rapidly depleting large contiguous blocks and leading to high external fragmentation when large processes request memory. First-Fit and Best-Fit generally exhibit superior memory utilization and lower long-term failure rates.
"""
