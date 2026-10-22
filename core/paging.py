from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any
import math


@dataclass
class FixedPartitioningResult:
    partition_size: int
    num_partitions: int
    total_memory: int
    satisfied_requests: int
    failed_requests: int
    total_internal_frag: int
    unusable_unallocated_memory: int
    utilization: float
    allocations: List[Dict[str, Any]]


@dataclass
class PagingOverheadResult:
    process_size_kb: int
    page_size_kb: int
    entry_size_bytes: int
    num_pages: int
    internal_frag_kb: int
    page_table_size_bytes: int
    overhead_percentage: float


@dataclass
class SegmentationOverheadResult:
    segments: List[Dict[str, Any]]  # name, size_kb
    entry_size_bytes: int
    total_process_size_kb: int
    num_segments: int
    internal_frag_kb: int
    segment_table_size_bytes: int


def calculate_fixed_partitioning(
    partition_size_kb: int,
    num_partitions: int,
    request_sizes_kb: List[int]
) -> FixedPartitioningResult:
    """Simulate fixed partitioning with equal partition sizes."""
    if partition_size_kb <= 0 or num_partitions <= 0:
        raise ValueError("Partition size and number of partitions must be positive integers.")
    if any(req <= 0 for req in request_sizes_kb):
        raise ValueError("Process request sizes must be positive integers.")

    total_mem = partition_size_kb * num_partitions
    occupied = 0
    total_internal_frag = 0
    satisfied = 0
    failed = 0
    allocations = []

    for idx, req in enumerate(request_sizes_kb):
        pid = f"P{idx + 1}"
        if req > partition_size_kb:
            failed += 1
            allocations.append({
                "pid": pid,
                "requested_kb": req,
                "partition_idx": None,
                "allocated_kb": 0,
                "internal_frag_kb": 0,
                "status": "Failed (Exceeds partition size)"
            })
        elif occupied < num_partitions:
            internal_frag = partition_size_kb - req
            total_internal_frag += internal_frag
            occupied += 1
            satisfied += 1
            allocations.append({
                "pid": pid,
                "requested_kb": req,
                "partition_idx": occupied - 1,
                "allocated_kb": partition_size_kb,
                "internal_frag_kb": internal_frag,
                "status": "Allocated"
            })
        else:
            failed += 1
            allocations.append({
                "pid": pid,
                "requested_kb": req,
                "partition_idx": None,
                "allocated_kb": 0,
                "internal_frag_kb": 0,
                "status": "Failed (Out of partitions)"
            })

    unallocated_slots = num_partitions - occupied
    unusable_unallocated = unallocated_slots * partition_size_kb
    actual_used = sum(a["requested_kb"] for a in allocations if a["status"] == "Allocated")
    utilization = round(actual_used / total_mem, 4) if total_mem > 0 else 0.0

    return FixedPartitioningResult(
        partition_size=partition_size_kb,
        num_partitions=num_partitions,
        total_memory=total_mem,
        satisfied_requests=satisfied,
        failed_requests=failed,
        total_internal_frag=total_internal_frag,
        unusable_unallocated_memory=unusable_unallocated,
        utilization=utilization,
        allocations=allocations
    )


def calculate_paging_overhead(
    process_size_kb: int,
    page_size_kb: int = 4,
    entry_size_bytes: int = 4
) -> PagingOverheadResult:
    """Calculate internal fragmentation and page table overhead for simple paging."""
    if page_size_kb <= 0 or process_size_kb <= 0 or entry_size_bytes <= 0:
        raise ValueError("Process size, page size, and entry size must be positive.")

    num_pages = math.ceil(process_size_kb / page_size_kb)
    remainder = process_size_kb % page_size_kb
    internal_frag = (page_size_kb - remainder) % page_size_kb

    page_table_bytes = num_pages * entry_size_bytes
    total_process_bytes = process_size_kb * 1024
    overhead_pct = round((page_table_bytes / total_process_bytes) * 100, 4) if total_process_bytes > 0 else 0.0

    return PagingOverheadResult(
        process_size_kb=process_size_kb,
        page_size_kb=page_size_kb,
        entry_size_bytes=entry_size_bytes,
        num_pages=num_pages,
        internal_frag_kb=internal_frag,
        page_table_size_bytes=page_table_bytes,
        overhead_percentage=overhead_pct
    )


def calculate_segmentation_overhead(
    segments: List[Dict[str, Any]],
    entry_size_bytes: int = 8
) -> SegmentationOverheadResult:
    """Calculate segmentation memory overhead (segments have 0 internal fragmentation)."""
    if entry_size_bytes <= 0:
        raise ValueError("Entry size must be positive.")
    if any(s.get("size_kb", 0) <= 0 for s in segments):
        raise ValueError("All segment sizes must be positive.")

    total_size = sum(s.get("size_kb", 0) for s in segments)
    num_segs = len(segments)
    table_bytes = num_segs * entry_size_bytes

    return SegmentationOverheadResult(
        segments=segments,
        entry_size_bytes=entry_size_bytes,
        total_process_size_kb=total_size,
        num_segments=num_segs,
        internal_frag_kb=0,  # Pure segmentation eliminates internal fragmentation
        segment_table_size_bytes=table_bytes
    )


def get_comparison_matrix() -> List[Dict[str, str]]:
    """Scores every memory management technique as specified in PRD F3."""
    return [
        {
            "Technique": "Fixed Partitioning",
            "Internal Fragmentation": "High (unused portion of allocated partition)",
            "External Fragmentation": "None (fixed slots)",
            "Speed / Complexity": "Fastest (simple table lookup)",
            "Hardware Overhead": "Minimal (limit registers)",
            "Flexibility": "Poor (fixed size limits process scalability)",
            "Compaction Required": "No"
        },
        {
            "Technique": "Dynamic Partitioning",
            "Internal Fragmentation": "Zero (partitions sized exactly to request)",
            "External Fragmentation": "Severe (holes scattered across memory)",
            "Speed / Complexity": "Moderate (search algorithms: Best/First/Worst)",
            "Hardware Overhead": "Low (base & limit registers)",
            "Flexibility": "Moderate (variable process sizes, but needs contiguous space)",
            "Compaction Required": "Yes (costly memory shuffling)"
        },
        {
            "Technique": "Paging (Pure)",
            "Internal Fragmentation": "Low (at most page_size - 1 in last frame)",
            "External Fragmentation": "Zero (any free frame can satisfy request)",
            "Speed / Complexity": "Fast (hardware MMU, TLB lookup)",
            "Hardware Overhead": "Moderate to High (Page tables, TLB)",
            "Flexibility": "High (non-contiguous physical allocation)",
            "Compaction Required": "No"
        },
        {
            "Technique": "Segmentation",
            "Internal Fragmentation": "Zero (segments matched to logical modules)",
            "External Fragmentation": "Moderate to High (variable segment sizes)",
            "Speed / Complexity": "Moderate (bounds checking + base offset)",
            "Hardware Overhead": "Low (Segment table base & limit)",
            "Flexibility": "High (matches logical modular code, code sharing)",
            "Compaction Required": "Yes (if external fragmentation is high)"
        },
        {
            "Technique": "Paged Segmentation",
            "Internal Fragmentation": "Low (last page of each segment)",
            "External Fragmentation": "Zero (pages placed anywhere)",
            "Speed / Complexity": "Slower without TLB (two table lookups)",
            "Hardware Overhead": "Highest (Segment table pointing to Page tables)",
            "Flexibility": "Maximum (modular sharing + non-contiguous frames)",
            "Compaction Required": "No"
        }
    ]
