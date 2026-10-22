import pytest
from core.replacement import (
    simulate_fifo,
    simulate_lru,
    simulate_optimal,
    STANDARD_REF_STRING,
    BELADY_REF_STRING
)


def test_standard_reference_string():
    """
    TRD requirement:
    Reference string 7,0,1,2,0,3,0,4,2,3,0,3,2,1,2,0,1,7,0,1 with 3 frames:
    FIFO: 15 faults
    LRU: 12 faults
    Optimal: 9 faults
    """
    fifo_res = simulate_fifo(STANDARD_REF_STRING, num_frames=3)
    lru_res = simulate_lru(STANDARD_REF_STRING, num_frames=3)
    opt_res = simulate_optimal(STANDARD_REF_STRING, num_frames=3)

    assert fifo_res.faults == 15
    assert fifo_res.hits == 5
    assert fifo_res.hit_ratio == round(5 / 20, 4)

    assert lru_res.faults == 12
    assert lru_res.hits == 8
    assert lru_res.hit_ratio == round(8 / 20, 4)

    assert opt_res.faults == 9
    assert opt_res.hits == 11
    assert opt_res.hit_ratio == round(11 / 20, 4)


def test_beladys_anomaly():
    """
    TRD requirement:
    Belady string 1,2,3,4,1,2,5,1,2,3,4,5 with FIFO:
    3 frames: 9 faults
    4 frames: 10 faults (verifies Belady's anomaly)
    """
    fifo_3 = simulate_fifo(BELADY_REF_STRING, num_frames=3)
    fifo_4 = simulate_fifo(BELADY_REF_STRING, num_frames=4)

    assert fifo_3.faults == 9
    assert fifo_4.faults == 10
    assert fifo_4.faults > fifo_3.faults  # Anomaly proven


def test_lru_hit_updates_recency():
    # 2 frames, ref: [1, 2, 1, 3]
    # 1 loaded, 2 loaded. Then 1 hits -> recency of 1 updated.
    # When 3 arrives, 2 must be evicted (LRU), NOT 1.
    res = simulate_lru([1, 2, 1, 3], num_frames=2)
    assert res.steps[2].is_fault is False  # Hit on 1
    assert res.steps[3].is_fault is True
    assert res.steps[3].evicted_page == 2  # 2 was evicted because 1 was recently used


def test_fifo_hit_does_not_reorder():
    # 2 frames, ref: [1, 2, 1, 3]
    # 1 loaded, 2 loaded. Then 1 hits -> FIFO must NOT move 1 to back of queue.
    # When 3 arrives, 1 entered first so 1 must be evicted.
    res = simulate_fifo([1, 2, 1, 3], num_frames=2)
    assert res.steps[2].is_fault is False  # Hit on 1
    assert res.steps[3].is_fault is True
    assert res.steps[3].evicted_page == 1  # 1 was earliest arrived, so evicted


def test_optimal_tie_break():
    # 3 frames, ref: [1, 2, 3, 4]
    # Pages 1, 2, 3 all loaded. At 4, none are used again.
    # Tie-break rule: evict earliest-entered page -> 1
    res = simulate_optimal([1, 2, 3, 4], num_frames=3)
    assert res.steps[3].is_fault is True
    assert res.steps[3].evicted_page == 1


def test_invalid_inputs_replacement():
    with pytest.raises(ValueError):
        simulate_fifo([1, 2, 3], num_frames=0)

    with pytest.raises(ValueError):
        simulate_lru([1, 2, 3], num_frames=-1)

    with pytest.raises(ValueError):
        simulate_optimal([1, -2, 3], num_frames=3)
