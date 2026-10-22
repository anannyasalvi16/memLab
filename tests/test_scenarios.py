import pytest
from core.scenarios import run_worst_fit_scenario, run_all_strategies_for_preset


def test_preset_worst_fit_scenario():
    """
    PRD & TRD requirement:
    Preset scenario: holes [100, 120] KB, requests [60, 50, 50, 50] KB.
    - Worst-fit satisfies all 4 requests.
    - First-fit, Best-fit, Next-fit must fail the last request.
    """
    results = run_all_strategies_for_preset()

    # Worst-fit must satisfy all 4
    wf = results["worst_fit"]
    assert wf.satisfied_count == 4
    assert wf.failed_count == 0
    assert wf.metrics.failure_rate == 0.0

    # First-fit fails the 4th request
    ff = results["first_fit"]
    assert ff.satisfied_count == 3
    assert ff.failed_count == 1
    assert ff.metrics.failure_rate == 0.25

    # Best-fit fails the 4th request
    bf = results["best_fit"]
    assert bf.satisfied_count == 3
    assert bf.failed_count == 1
    assert bf.metrics.failure_rate == 0.25

    # Next-fit fails the 4th request
    nf = results["next_fit"]
    assert nf.satisfied_count == 3
    assert nf.failed_count == 1
    assert nf.metrics.failure_rate == 0.25


def test_step_by_step_worst_fit_trace():
    """Verify exact step-by-step block allocations in Worst-Fit."""
    wf = run_worst_fit_scenario("worst_fit")
    events = wf.events

    # Step 1: Init
    assert events[0].action == "INIT"
    # Step 2: Allocate 60 KB to P1 in 120 KB hole -> leaves 60 KB hole
    assert events[1].pid == "P1"
    assert events[1].success is True
    # Step 3: Allocate 50 KB to P2 in 100 KB hole -> leaves 50 KB hole
    assert events[2].pid == "P2"
    assert events[2].success is True
    # Step 4: Allocate 50 KB to P3 in 60 KB hole -> leaves 10 KB hole
    assert events[3].pid == "P3"
    assert events[3].success is True
    # Step 5: Allocate 50 KB to P4 in 50 KB hole -> leaves 0 KB (exact fit)
    assert events[4].pid == "P4"
    assert events[4].success is True


def test_worst_fit_counterexample_proof():
    from core.benchmark import get_worst_fit_counterexample
    counter = get_worst_fit_counterexample()
    results = counter["results"]
    # Worst-Fit must perform strictly worse than Best-Fit (more failures)
    assert results["worst_fit"]["failed"] > results["best_fit"]["failed"]
    assert results["worst_fit"]["failure_rate"] > results["best_fit"]["failure_rate"]
