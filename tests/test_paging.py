import pytest
from core.paging import (
    calculate_fixed_partitioning,
    calculate_paging_overhead,
    calculate_segmentation_overhead
)


def test_fixed_partitioning():
    # 4 partitions of 100 KB each. Total 400 KB.
    # Requests: 80, 50, 120 (fails), 90
    res = calculate_fixed_partitioning(
        partition_size_kb=100,
        num_partitions=4,
        request_sizes_kb=[80, 50, 120, 90]
    )
    assert res.satisfied_requests == 3
    assert res.failed_requests == 1
    # Internal frag: (100-80) + (100-50) + (100-90) = 20 + 50 + 10 = 80 KB
    assert res.total_internal_frag == 80


def test_paging_overhead():
    # Process 10 KB, Page size 4 KB
    # Pages needed: ceil(10 / 4) = 3 pages (total 12 KB)
    # Internal fragmentation: 12 - 10 = 2 KB
    # Page table size: 3 pages * 4 bytes = 12 bytes
    res = calculate_paging_overhead(
        process_size_kb=10,
        page_size_kb=4,
        entry_size_bytes=4
    )
    assert res.num_pages == 3
    assert res.internal_frag_kb == 2
    assert res.page_table_size_bytes == 12


def test_segmentation_overhead():
    segments = [
        {"name": "Code", "size_kb": 64},
        {"name": "Data", "size_kb": 32},
        {"name": "Stack", "size_kb": 16},
    ]
    res = calculate_segmentation_overhead(segments, entry_size_bytes=8)
    assert res.num_segments == 3
    assert res.total_process_size_kb == 112
    assert res.internal_frag_kb == 0  # No internal fragmentation
    assert res.segment_table_size_bytes == 24  # 3 * 8


def test_paging_exact_fit():
    # Exact fit: 16 KB process with 4 KB pages -> exactly 4 pages, 0 waste
    res = calculate_paging_overhead(
        process_size_kb=16,
        page_size_kb=4,
        entry_size_bytes=4
    )
    assert res.num_pages == 4
    assert res.internal_frag_kb == 0


def test_invalid_inputs_paging():
    # Negative/zero process or page size
    with pytest.raises(ValueError):
        calculate_paging_overhead(process_size_kb=-10, page_size_kb=4)

    with pytest.raises(ValueError):
        calculate_paging_overhead(process_size_kb=10, page_size_kb=0)

    # Fixed partitioning invalid arguments
    with pytest.raises(ValueError):
        calculate_fixed_partitioning(partition_size_kb=0, num_partitions=4, request_sizes_kb=[10])

    with pytest.raises(ValueError):
        calculate_fixed_partitioning(partition_size_kb=100, num_partitions=-1, request_sizes_kb=[10])

    with pytest.raises(ValueError):
        calculate_fixed_partitioning(partition_size_kb=100, num_partitions=4, request_sizes_kb=[-5])
