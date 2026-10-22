from __future__ import annotations
import random
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from core.allocator import MemoryAllocator


@dataclass
class BenchmarkResult:
    strategy: str
    runs: int
    avg_failure_rate: float
    avg_external_fragmentation: float
    avg_utilization: float
    total_satisfied: int
    total_failed: int
    total_allocated_kb: int


def generate_workload(
    num_operations: int,
    total_memory_kb: int,
    min_size_kb: int = 10,
    max_size_kb: int = 80,
    free_probability: float = 0.35,
    seed: int = 42
) -> List[Tuple[str, str, int]]:
    """
    Generates a deterministic sequence of (action, pid, size) requests.
    action: 'ALLOC' or 'FREE'
    """
    rng = random.Random(seed)
    workload: List[Tuple[str, str, int]] = []
    active_pids: List[str] = []
    pid_counter = 1

    for _ in range(num_operations):
        # Decide whether to allocate or free
        can_free = bool(active_pids)
        if can_free and rng.random() < free_probability:
            # Free an active process
            pid_to_free = rng.choice(active_pids)
            active_pids.remove(pid_to_free)
            workload.append(("FREE", pid_to_free, 0))
        else:
            # Allocate
            pid = f"PROC_{pid_counter}"
            pid_counter += 1
            size = rng.randint(min_size_kb, max_size_kb)
            active_pids.append(pid)
            workload.append(("ALLOC", pid, size))

    return workload


def run_single_workload(
    workload: List[Tuple[str, str, int]],
    total_memory_kb: int,
    strategy: str,
    record_events: bool = False
) -> Dict[str, Any]:
    """Applies a workload to a strategy and returns performance metrics."""
    allocator = MemoryAllocator(total_size=total_memory_kb, strategy=strategy, record_events=record_events)
    for action, pid, size in workload:
        if action == "ALLOC":
            allocator.allocate(size=size, pid=pid)
        elif action == "FREE":
            allocator.free(pid=pid)

    m = allocator.metrics
    return {
        "strategy": strategy,
        "failure_rate": m.failure_rate,
        "external_fragmentation": m.external_fragmentation,
        "utilization": m.utilization,
        "satisfied": m.requests_satisfied,
        "failed": m.requests_failed,
        "allocated_kb": m.allocated_memory
    }


def run_benchmark_suite(
    num_runs: int = 20,
    num_operations_per_run: int = 50,
    total_memory_kb: int = 500,
    min_size_kb: int = 20,
    max_size_kb: int = 120,
    base_seed: int = 100
) -> Tuple[List[BenchmarkResult], List[Dict[str, Any]]]:
    """
    Executes multiple Monte Carlo benchmark runs across all 4 allocation strategies.
    Returns (aggregated_results, detailed_run_records).
    """
    strategies = ["first_fit", "best_fit", "worst_fit", "next_fit"]
    raw_records: List[Dict[str, Any]] = []

    for run_idx in range(num_runs):
        workload = generate_workload(
            num_operations=num_operations_per_run,
            total_memory_kb=total_memory_kb,
            min_size_kb=min_size_kb,
            max_size_kb=max_size_kb,
            seed=base_seed + run_idx
        )
        for strat in strategies:
            res = run_single_workload(workload, total_memory_kb, strat, record_events=False)
            res["run_id"] = run_idx + 1
            raw_records.append(res)

    # Aggregate by strategy
    aggregated: List[BenchmarkResult] = []
    for strat in strategies:
        strat_records = [r for r in raw_records if r["strategy"] == strat]
        n = len(strat_records)
        avg_fail = sum(r["failure_rate"] for r in strat_records) / n
        avg_frag = sum(r["external_fragmentation"] for r in strat_records) / n
        avg_util = sum(r["utilization"] for r in strat_records) / n
        tot_sat = sum(r["satisfied"] for r in strat_records)
        tot_fail = sum(r["failed"] for r in strat_records)
        tot_alloc = sum(r["allocated_kb"] for r in strat_records)

        aggregated.append(BenchmarkResult(
            strategy=strat.replace("_", " ").title(),
            runs=num_runs,
            avg_failure_rate=round(avg_fail, 4),
            avg_external_fragmentation=round(avg_frag, 4),
            avg_utilization=round(avg_util, 4),
            total_satisfied=tot_sat,
            total_failed=tot_fail,
            total_allocated_kb=tot_alloc
        ))

    return aggregated, raw_records


FIXED_COUNTEREXAMPLE_WORKLOAD: List[Tuple[str, str, int]] = [
    ("ALLOC", "PROC_1", 82),
    ("ALLOC", "PROC_2", 84),
    ("ALLOC", "PROC_3", 49),
    ("FREE", "PROC_3", 0),
    ("ALLOC", "PROC_4", 48),
    ("FREE", "PROC_2", 0),
    ("FREE", "PROC_1", 0),
    ("ALLOC", "PROC_5", 75),
    ("ALLOC", "PROC_6", 45),
    ("ALLOC", "PROC_7", 92),
    ("FREE", "PROC_4", 0),
    ("FREE", "PROC_5", 0),
    ("ALLOC", "PROC_8", 84),
    ("FREE", "PROC_8", 0),
    ("ALLOC", "PROC_9", 91),
]


def get_worst_fit_counterexample() -> Dict[str, Any]:
    """
    Returns an empirical workload where Worst-Fit performs strictly worse
    than Best-Fit, proving why Worst-Fit is not universally optimal.
    """
    total_mem = 300
    workload = FIXED_COUNTEREXAMPLE_WORKLOAD

    results = {}
    for strat in ["first_fit", "best_fit", "worst_fit", "next_fit"]:
        results[strat] = run_single_workload(workload, total_mem, strat, record_events=False)

    return {
        "workload_length": len(workload),
        "total_memory_kb": total_mem,
        "results": results
    }
