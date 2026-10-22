import pytest
from core.allocator import MemoryAllocator
from core.models import Block


def test_first_fit():
    # Holes: 100, 200, 300
    blocks = [
        Block(0, 100, None),
        Block(100, 50, "P0"),
        Block(150, 200, None),
        Block(350, 50, "P1"),
        Block(400, 300, None),
    ]
    alloc = MemoryAllocator.from_blocks(blocks, strategy="first_fit")
    # Request 150 -> should skip 100, pick 200
    b = alloc.allocate(150, "P_new")
    assert b is not None
    assert b.start == 150
    assert b.size == 150
    assert alloc.metrics.requests_satisfied == 1


def test_best_fit():
    # Holes: 100, 300, 150
    blocks = [
        Block(0, 100, None),
        Block(100, 50, "P0"),
        Block(150, 300, None),
        Block(450, 50, "P1"),
        Block(500, 150, None),
    ]
    alloc = MemoryAllocator.from_blocks(blocks, strategy="best_fit")
    # Request 120 -> best is 150 (leaves 30), not 300 (leaves 180)
    b = alloc.allocate(120, "P_new")
    assert b is not None
    assert b.start == 500
    assert b.size == 120


def test_worst_fit():
    # Holes: 100, 300, 150
    blocks = [
        Block(0, 100, None),
        Block(100, 50, "P0"),
        Block(150, 300, None),
        Block(450, 50, "P1"),
        Block(500, 150, None),
    ]
    alloc = MemoryAllocator.from_blocks(blocks, strategy="worst_fit")
    # Request 120 -> worst is 300 (leaves 180)
    b = alloc.allocate(120, "P_new")
    assert b is not None
    assert b.start == 150
    assert b.size == 120


def test_next_fit_wraparound():
    # Holes at 0 (size 50), 200 (size 50), 400 (size 50)
    blocks = [
        Block(0, 50, None),
        Block(50, 150, "P0"),
        Block(200, 50, None),
        Block(250, 150, "P1"),
        Block(400, 50, None),
    ]
    alloc = MemoryAllocator.from_blocks(blocks, strategy="next_fit")
    # First allocation (50 KB): fills hole at 0 completely. Last pos = 50.
    b1 = alloc.allocate(50, "A")
    assert b1.start == 0

    # Second allocation (50 KB): search starts from 50 -> picks hole at 200. Last pos = 250.
    b2 = alloc.allocate(50, "B")
    assert b2.start == 200

    # Third allocation (50 KB): search starts from 250 -> picks hole at 400. Last pos = 450.
    b3 = alloc.allocate(50, "C")
    assert b3.start == 400

    # Fourth allocation (50 KB): no holes after 450.
    # Now free A (at 0..50) so there is a hole at 0.
    alloc.free("A")
    # Search starts from 450 -> wraps around to 0!
    b4 = alloc.allocate(50, "D")
    assert b4.start == 0



def test_hole_merging_on_free():
    alloc = MemoryAllocator(total_size=300, strategy="first_fit")
    alloc.allocate(100, "P1")
    alloc.allocate(100, "P2")
    alloc.allocate(100, "P3")
    assert len(alloc.blocks) == 3
    assert all(not b.is_free for b in alloc.blocks)

    # Free middle block P2 -> single hole between P1 and P3
    alloc.free("P2")
    assert len(alloc.blocks) == 3
    assert alloc.blocks[1].is_free
    assert alloc.blocks[1].size == 100

    # Free P1 -> merges with P2 hole!
    alloc.free("P1")
    assert len(alloc.blocks) == 2
    assert alloc.blocks[0].is_free
    assert alloc.blocks[0].size == 200

    # Free P3 -> merges completely into 300 KB hole
    alloc.free("P3")
    assert len(alloc.blocks) == 1
    assert alloc.blocks[0].is_free
    assert alloc.blocks[0].size == 300


def test_allocation_failure():
    alloc = MemoryAllocator(total_size=100, strategy="first_fit")
    b = alloc.allocate(150, "TooBig")
    assert b is None
    assert alloc.metrics.requests_failed == 1
    assert alloc.metrics.failure_rate == 1.0


def test_division_by_zero_guards():
    # Zero requests: failure_rate should be 0.0, not error
    alloc = MemoryAllocator(total_size=100, strategy="first_fit")
    assert alloc.metrics.requests_satisfied == 0
    assert alloc.metrics.requests_failed == 0
    assert alloc.metrics.failure_rate == 0.0

    # Full memory: total_free == 0, external_fragmentation should be 0.0, not error
    b = alloc.allocate(100, "Full")
    assert b is not None
    assert alloc.metrics.free_memory == 0
    assert alloc.metrics.external_fragmentation == 0.0


def test_next_fit_pointer_after_free_and_coalesce():
    alloc = MemoryAllocator(total_size=300, strategy="next_fit")
    alloc.allocate(50, "P1")  # 0..50, last_pos = 50
    alloc.allocate(50, "P2")  # 50..100, last_pos = 100
    alloc.allocate(50, "P3")  # 100..150, last_pos = 150

    # Free P2 and P3 -> coalesce into hole 50..150
    alloc.free("P2")
    alloc.free("P3")

    # Pointer should snap or wrap safely to valid hole, not crash or skip
    assert alloc.last_alloc_address <= alloc.total_size
    b_new = alloc.allocate(60, "P_new")
    assert b_new is not None
    assert alloc.metrics.requests_satisfied == 4


def test_invalid_inputs_allocator():
    alloc = MemoryAllocator(total_size=100, strategy="first_fit")

    # Reject size <= 0
    assert alloc.allocate(0, "P_zero") is None
    assert alloc.allocate(-10, "P_neg") is None
    assert alloc.failed_count == 2

    # Reject duplicate PID
    b1 = alloc.allocate(30, "P1")
    assert b1 is not None
    assert alloc.allocate(20, "P1") is None
    assert alloc.failed_count == 3

    # Reject request > total_size
    assert alloc.allocate(200, "P_huge") is None
    assert alloc.failed_count == 4

    # Free unknown PID
    assert alloc.free("Unknown") is False
