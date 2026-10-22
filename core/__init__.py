# MemLab Core Package
from core.models import Block, AllocationMetrics, AllocationEvent
from core.allocator import MemoryAllocator
from core.scenarios import run_worst_fit_scenario, run_all_strategies_for_preset
from core.replacement import simulate_replacement, simulate_fifo, simulate_lru, simulate_optimal
from core.paging import calculate_fixed_partitioning, calculate_paging_overhead, calculate_segmentation_overhead
from core.benchmark import run_benchmark_suite, generate_workload

__all__ = [
    "Block",
    "AllocationMetrics",
    "AllocationEvent",
    "MemoryAllocator",
    "run_worst_fit_scenario",
    "run_all_strategies_for_preset",
    "simulate_replacement",
    "simulate_fifo",
    "simulate_lru",
    "simulate_optimal",
    "calculate_fixed_partitioning",
    "calculate_paging_overhead",
    "calculate_segmentation_overhead",
    "run_benchmark_suite",
    "generate_workload",
]
