from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any


@dataclass
class PageStep:
    step_index: int
    page: int
    frames: List[Optional[int]]
    is_fault: bool
    evicted_page: Optional[int] = None


@dataclass
class PageReplacementResult:
    algorithm: str
    num_frames: int
    reference_string: List[int]
    total_references: int
    faults: int
    hits: int
    hit_ratio: float
    steps: List[PageStep] = field(default_factory=list)


def simulate_fifo(pages: List[int], num_frames: int) -> PageReplacementResult:
    """FIFO Page Replacement Simulator."""
    if num_frames <= 0:
        raise ValueError("Number of frames must be positive (at least 1).")
    if any(p < 0 for p in pages):
        raise ValueError("Page numbers must be non-negative integers.")

    frames: List[Optional[int]] = [None] * num_frames
    fifo_queue: List[int] = []  # tracks insertion order of frame indices
    steps: List[PageStep] = []
    faults = 0
    hits = 0

    for idx, page in enumerate(pages):
        evicted = None
        if page in frames:
            hits += 1
            is_fault = False
        else:
            faults += 1
            is_fault = True
            # Find empty slot or evict
            if None in frames:
                empty_idx = frames.index(None)
                frames[empty_idx] = page
                fifo_queue.append(empty_idx)
            else:
                evict_slot = fifo_queue.pop(0)
                evicted = frames[evict_slot]
                frames[evict_slot] = page
                fifo_queue.append(evict_slot)

        steps.append(PageStep(
            step_index=idx,
            page=page,
            frames=list(frames),
            is_fault=is_fault,
            evicted_page=evicted
        ))

    hit_ratio = round(hits / len(pages), 4) if pages else 0.0
    return PageReplacementResult(
        algorithm="FIFO",
        num_frames=num_frames,
        reference_string=pages,
        total_references=len(pages),
        faults=faults,
        hits=hits,
        hit_ratio=hit_ratio,
        steps=steps
    )


def simulate_lru(pages: List[int], num_frames: int) -> PageReplacementResult:
    """Least Recently Used (LRU) Page Replacement Simulator."""
    if num_frames <= 0:
        raise ValueError("Number of frames must be positive (at least 1).")
    if any(p < 0 for p in pages):
        raise ValueError("Page numbers must be non-negative integers.")

    frames: List[Optional[int]] = [None] * num_frames
    last_used: Dict[int, int] = {}  # page -> last used step_index
    steps: List[PageStep] = []
    faults = 0
    hits = 0

    for idx, page in enumerate(pages):
        evicted = None
        if page in frames:
            hits += 1
            is_fault = False
            last_used[page] = idx
        else:
            faults += 1
            is_fault = True
            if None in frames:
                empty_idx = frames.index(None)
                frames[empty_idx] = page
            else:
                # Find page currently in frames with smallest last_used
                lru_page = min(
                    [p for p in frames if p is not None],
                    key=lambda p: last_used.get(p, -1)
                )
                evict_slot = frames.index(lru_page)
                evicted = lru_page
                frames[evict_slot] = page

            last_used[page] = idx

        steps.append(PageStep(
            step_index=idx,
            page=page,
            frames=list(frames),
            is_fault=is_fault,
            evicted_page=evicted
        ))

    hit_ratio = round(hits / len(pages), 4) if pages else 0.0
    return PageReplacementResult(
        algorithm="LRU",
        num_frames=num_frames,
        reference_string=pages,
        total_references=len(pages),
        faults=faults,
        hits=hits,
        hit_ratio=hit_ratio,
        steps=steps
    )


def simulate_optimal(pages: List[int], num_frames: int) -> PageReplacementResult:
    """Optimal (Belady's MIN) Page Replacement Simulator."""
    if num_frames <= 0:
        raise ValueError("Number of frames must be positive (at least 1).")
    if any(p < 0 for p in pages):
        raise ValueError("Page numbers must be non-negative integers.")

    frames: List[Optional[int]] = [None] * num_frames
    arrival_order: Dict[int, int] = {}  # page -> step_index when loaded into frame
    steps: List[PageStep] = []
    faults = 0
    hits = 0

    for idx, page in enumerate(pages):
        evicted = None
        if page in frames:
            hits += 1
            is_fault = False
        else:
            faults += 1
            is_fault = True
            if None in frames:
                empty_idx = frames.index(None)
                frames[empty_idx] = page
                arrival_order[page] = idx
            else:
                # Find page that will not be used for longest time in future
                future_occurrences: Dict[int, int] = {}
                for p in frames:
                    if p is None:
                        continue
                    # Find next occurrence index after current idx
                    try:
                        next_use = pages.index(p, idx + 1)
                        future_occurrences[p] = next_use
                    except ValueError:
                        future_occurrences[p] = float("inf")  # never used again

                # Choose page with maximum future distance; tie-break: evict earliest-entered page
                def victim_key(p: int) -> Tuple[float, float]:
                    dist = future_occurrences[p]
                    if dist == float("inf"):
                        return (float("inf"), -float(arrival_order.get(p, 0)))
                    return (float(dist), 0.0)

                victim = max(
                    [p for p in frames if p is not None],
                    key=victim_key
                )
                evict_slot = frames.index(victim)
                evicted = victim
                frames[evict_slot] = page
                arrival_order[page] = idx

        steps.append(PageStep(
            step_index=idx,
            page=page,
            frames=list(frames),
            is_fault=is_fault,
            evicted_page=evicted
        ))

    hit_ratio = round(hits / len(pages), 4) if pages else 0.0
    return PageReplacementResult(
        algorithm="Optimal",
        num_frames=num_frames,
        reference_string=pages,
        total_references=len(pages),
        faults=faults,
        hits=hits,
        hit_ratio=hit_ratio,
        steps=steps
    )


def simulate_replacement(algorithm: str, pages: List[int], num_frames: int) -> PageReplacementResult:
    algo = algorithm.upper()
    if algo == "FIFO":
        return simulate_fifo(pages, num_frames)
    elif algo == "LRU":
        return simulate_lru(pages, num_frames)
    elif algo in ("OPTIMAL", "OPT"):
        return simulate_optimal(pages, num_frames)
    else:
        raise ValueError(f"Unknown page replacement algorithm: {algorithm}")


# Preset benchmark strings from TRD
STANDARD_REF_STRING = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
BELADY_REF_STRING = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]


def run_belady_check(max_frames: int = 7) -> List[Dict[str, Any]]:
    """Evaluates FIFO faults across varying frame sizes to demonstrate Belady's Anomaly."""
    data = []
    for f in range(1, max_frames + 1):
        res_fifo = simulate_fifo(BELADY_REF_STRING, f)
        res_lru = simulate_lru(BELADY_REF_STRING, f)
        res_opt = simulate_optimal(BELADY_REF_STRING, f)
        data.append({
            "frames": f,
            "FIFO Faults": res_fifo.faults,
            "LRU Faults": res_lru.faults,
            "Optimal Faults": res_opt.faults,
            "FIFO Anomaly": "Yes (Increased!)" if (f == 4 and res_fifo.faults > 9) else "No"
        })
    return data
